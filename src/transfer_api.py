from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db
import math

transfer_bp = Blueprint('transfer', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

@transfer_bp.route('/transfers', methods=['GET'])
def get_transfers():
    """
    Get all transfers
    ---
    tags:
      - Transfers
    responses:
      200:
        description: Success
    """
    data = query_db("SELECT * FROM Transfer_Orders")

    return jsonify({
        "success": True,
        "data": data
    })

@transfer_bp.route('/transfers', methods=['POST'])
def create_transfer():
    """
    Create transfer order
    ---
    tags:
      - Transfers
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - from_warehouse_id
            - to_warehouse_id
            - staff_id
            - products
          properties:
            from_warehouse_id:
              type: integer
            to_warehouse_id:
              type: integer
            staff_id:
              type: integer
            products:
              type: array
              items:
                type: object
                properties:
                  product_id:
                    type: integer
                  quantity:
                    type: integer
    responses:
      200:
        description: Created
      400:
        description: Invalid input
    """
    data = request.json
    if not data:
        abort(400, "Invalid JSON")

    required = ["from_warehouse_id", "to_warehouse_id", "staff_id", "products"]
    if not all(k in data for k in required):
        abort(400, "Missing fields")

    # check kho tồn tại
    from_wh = query_db("SELECT * FROM Warehouses WHERE id=?", (data['from_warehouse_id'],), one=True)
    to_wh = query_db("SELECT * FROM Warehouses WHERE id=?", (data['to_warehouse_id'],), one=True)

    if not from_wh or not to_wh:
        abort(404, "Warehouse not found")

    # tạo lệnh (status = PENDING)
    execute_db(
        """
        INSERT INTO Transfer_Orders (from_warehouse_id, to_warehouse_id, staff_id, status)
        VALUES (?, ?, ?, 'PENDING')
        """,
        (data['from_warehouse_id'], data['to_warehouse_id'], data['staff_id'])
    )

    # lấy id mới nhất
    transfer = query_db("SELECT TOP 1 * FROM Transfer_Orders ORDER BY id DESC", one=True)
    transfer_id = transfer['id']

    for item in data['products']:
        product_id = item['product_id']
        qty = item['quantity']

        stock = query_db(
            "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
            (data['from_warehouse_id'], product_id),
            one=True
        )

        if not stock or stock['quantity'] < qty:
            abort(400, f"Not enough stock for product {product_id}")

        # TRỪ KHO
        execute_db(
            """
            UPDATE Inventory
            SET quantity = quantity - ?
            WHERE warehouse_id=? AND product_id=?
            """,
            (qty, data['from_warehouse_id'], product_id)
        )

        # lưu chi tiết
        execute_db(
            """
            INSERT INTO Transfer_Details (transfer_id, product_id, quantity)
            VALUES (?, ?, ?)
            """,
            (transfer_id, product_id, qty)
        )

    return jsonify({
        "success": True,
        "data": {
            "transfer_id": transfer_id,
            "status": "PENDING"
        }
    })

@transfer_bp.route('/transfers/suggest', methods=['GET'])
def suggest_warehouse():
    """
    Suggest best warehouse
    ---
    tags:
      - Transfers
    parameters:
      - in: query
        name: product_id
        type: integer
        required: true
      - in: query
        name: to_warehouse_id
        type: integer
        required: true
    responses:
      200:
        description: Success
      400:
        description: Invalid input
    """
    # FIX: ép kiểu int
    product_id = request.args.get('product_id', type=int)
    to_warehouse_id = request.args.get('to_warehouse_id', type=int)

    if not product_id or not to_warehouse_id:
        abort(400, "Missing params")

    target = query_db(
        "SELECT * FROM Warehouses WHERE id=?",
        (to_warehouse_id,),
        one=True
    )

    if not target:
        abort(404, "Target warehouse not found")

    inventories = query_db(
        """
        SELECT i.*, w.Latitude, w.Longitude
        FROM Inventory i
        JOIN Warehouses w ON i.warehouse_id = w.id
        WHERE product_id=? AND quantity > 0
        """,
        (product_id,)
    )

    best = None
    best_score = None

    for inv in inventories:
        dist = calculate_distance(
            inv['Latitude'], inv['Longitude'],
            target['Latitude'], target['Longitude']
        )

        # ưu tiên gần + nhiều hàng
        score = dist - inv['quantity'] * 0.01

        if best_score is None or score < best_score:
            best_score = score
            best = inv

    return jsonify({
        "success": True,
        "data": best
    })