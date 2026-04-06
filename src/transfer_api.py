from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db, get_db_connection
import math

transfer_bp = Blueprint('transfer', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

VALID_STATUS = ["PENDING", "APPROVED"]
@transfer_bp.route('/', methods=['GET'])
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

@transfer_bp.route('/', methods=['POST'])
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

    execute_db(
        """
        INSERT INTO Transfer_Orders (from_warehouse_id, to_warehouse_id, staff_id, status)
        VALUES (?, ?, ?, 'PENDING')
        """,
        (data['from_warehouse_id'], data['to_warehouse_id'], data['staff_id'])
    )

    transfer = query_db("SELECT TOP 1 * FROM Transfer_Orders ORDER BY id DESC", one=True)
    transfer_id = transfer['id']

    for item in data['products']:
        product_id = item['product_id']
        qty = item['quantity']

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


@transfer_bp.route('/<int:id>', methods=['PUT'])

def update_transfer_status(id):
    """
        Update transfer status
        ---
        tags:
          - Transfers
        parameters:
          - in: path
            name: id
            type: integer
            required: true
            description: Transfer order ID
          - in: body
            name: body
            schema:
              type: object
              required:
                - status
              properties:
                status:
                  type: string
                  enum: ["PENDING", "APPROVED"]
                  example: "APPROVED"
        responses:
          200:
            description: Status updated
          400:
            description: Invalid input or not enough stock
          404:
            description: Transfer not found
          500:
            description: Update failed
        """
    data = request.json
    if not data or 'status' not in data:
        return jsonify({"success": False, "message": "Missing status"}), 400

    status = data['status']
    if status not in VALID_STATUS:
        return jsonify({"success": False, "message": "Invalid status"}), 400

    transfer = query_db(
        "SELECT * FROM Transfer_Orders WHERE id=?",
        (id,),
        one=True
    )

    if not transfer:
        return jsonify({"success": False, "message": "Transfer not found"}), 404

    old_status = transfer['status']

    if old_status == status:
        return jsonify({"success": True, "data": "Status unchanged"})

    if old_status == "APPROVED" and status != "APPROVED":
        return jsonify({
            "success": False,
            "message": "Cannot change status after APPROVED"
        }), 400

    # ================== APPROVED ==================
    if status == "APPROVED":
        details = query_db(
            "SELECT * FROM Transfer_Details WHERE transfer_id=?",
            (id,)
        )

        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            for item in details:
                cursor.execute(
                    "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
                    (transfer['from_warehouse_id'], item['product_id'])
                )
                stock = cursor.fetchone()

                # ⚠️ pyodbc -> tuple => stock[0]
                if not stock or stock[0] < item['quantity']:
                    conn.rollback()
                    return jsonify({
                        "success": False,
                        "message": f"Not enough stock for product {item['product_id']}"
                    }), 400

            for item in details:
                cursor.execute(
                    "UPDATE Inventory SET quantity = quantity - ? WHERE warehouse_id=? AND product_id=?",
                    (item['quantity'], transfer['from_warehouse_id'], item['product_id'])
                )

            conn.commit()

        except Exception as e:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    # ================== UPDATE STATUS ==================
    execute_db(
        "UPDATE Transfer_Orders SET status=? WHERE id=?",
        (status, id)
    )

    return jsonify({
        "success": True,
        "data": {
            "transfer_id": id,
            "status": status
        }
    })

@transfer_bp.route('/suggest', methods=['GET'])
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
@transfer_bp.route('/<int:id>', methods=['DELETE'])
def delete_transfer(id):
    transfer = query_db(
        "SELECT * FROM Transfer_Orders WHERE id=?",
        (id,),
        one=True
    )

    if not transfer:
        abort(404, "Transfer not found")

    if transfer['status'] == "APPROVED":
        abort(400, "Cannot delete approved transfer")

    # xoá detail trước (FK)
    execute_db(
        "DELETE FROM Transfer_Details WHERE transfer_id=?",
        (id,)
    )

    # xoá transfer
    execute_db(
        "DELETE FROM Transfer_Orders WHERE id=?",
        (id,)
    )

    return jsonify({
        "success": True,
        "data": "Transfer deleted"
    })