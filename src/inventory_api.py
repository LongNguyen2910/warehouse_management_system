from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db

inventory_bp = Blueprint('inventory', __name__)

# ================= GET ALL =================
@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    """
    Get all inventory items
    ---
    tags:
      - Inventory
    responses:
      200:
        description: Danh sách toàn bộ tồn kho
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  warehouse_id:
                    type: integer
                    example: 2
                  product_id:
                    type: integer
                    example: 3
                  warehouse_name:
                    type: string
                    example: "Main Warehouse"
                  product_name:
                    type: string
                    example: "Product A"
                  quantity:
                    type: integer
                    example: 100
        """
    sql = """
        SELECT 
            i.id,
            i.warehouse_id,
            i.product_id,
            w.name AS warehouse_name,
            p.name AS product_name,
            i.quantity
        FROM Inventory i
        JOIN Warehouses w ON i.warehouse_id = w.id
        JOIN Products p ON i.product_id = p.id
        ORDER BY i.id DESC
    """
    data = query_db(sql)

    return jsonify({"success": True, "data": data})


# ================= ADD (CỘNG KHO) =================
@inventory_bp.route('/add', methods=['POST'])
def add_inventory():
    """
    Add inventory (increase quantity)
    ---
    tags:
      - Inventory
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - warehouse_name
            - product_name
            - quantity
          properties:
            warehouse_name:
              type: string
              example: "Main Warehouse"
            product_name:
              type: string
              example: "Product A"
            quantity:
              type: integer
              example: 50
    responses:
      200:
        description: Added successfully
      400:
        description: Missing fields or not found
      500:
        description: Add failed
    """
    data = request.json

    warehouse_name = data.get("warehouse_name")
    product_name = data.get("product_name")
    quantity = data.get("quantity")

    if not all([warehouse_name, product_name, quantity]):
        abort(400, "Missing fields")

    warehouse = query_db(
        "SELECT id FROM Warehouses WHERE name=?",
        (warehouse_name,),
        one=True
    )

    product = query_db(
        "SELECT id FROM Products WHERE name=?",
        (product_name,),
        one=True
    )

    if not warehouse or not product:
        abort(400, "Warehouse or Product not found")

    warehouse_id = warehouse["id"]
    product_id = product["id"]

    exist = query_db(
        "SELECT id FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (warehouse_id, product_id),
        one=True
    )

    if exist:
        success = execute_db(
            "UPDATE Inventory SET quantity = quantity + ? WHERE id=?",
            (quantity, exist['id'])
        )
    else:
        success = execute_db(
            "INSERT INTO Inventory (warehouse_id, product_id, quantity) VALUES (?,?,?)",
            (warehouse_id, product_id, quantity)
        )

    if not success:
        abort(500, "Add failed")

    return jsonify({"success": True, "message": "Added successfully"})


# ================= REMOVE (TRỪ KHO) =================
@inventory_bp.route('/remove', methods=['POST'])
def remove_inventory():
    """
    Remove inventory (decrease quantity)
    ---
    tags:
      - Inventory
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - warehouse_name
            - product_name
            - quantity
          properties:
            warehouse_name:
              type: string
              example: "Main Warehouse"
            product_name:
              type: string
              example: "Product A"
            quantity:
              type: integer
              example: 20
    responses:
      200:
        description: Removed successfully
      400:
        description: Missing fields, not found, or insufficient stock
      500:
        description: Remove failed
    """
    data = request.json

    warehouse_name = data.get("warehouse_name")
    product_name = data.get("product_name")
    quantity = data.get("quantity")

    if not all([warehouse_name, product_name, quantity]):
        abort(400, "Missing fields")

    warehouse = query_db(
        "SELECT id FROM Warehouses WHERE name=?",
        (warehouse_name,),
        one=True
    )

    product = query_db(
        "SELECT id FROM Products WHERE name=?",
        (product_name,),
        one=True
    )

    if not warehouse or not product:
        abort(400, "Warehouse or Product not found")

    inventory = query_db(
        "SELECT id, quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (warehouse["id"], product["id"]),
        one=True
    )

    if not inventory:
        abort(400, "Product not in warehouse")

    if inventory["quantity"] < quantity:
        abort(400, "Not enough stock")

    success = execute_db(
        "UPDATE Inventory SET quantity = quantity - ? WHERE id=?",
        (quantity, inventory["id"])
    )

    if not success:
        abort(500, "Remove failed")

    return jsonify({"success": True, "message": "Removed successfully"})

@inventory_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_inventory(id):
    """
    Delete inventory item
    ---
    tags:
      - Inventory
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID của inventory cần xóa
        example: 1
    responses:
      200:
        description: Deleted successfully
      404:
        description: Inventory not found
      500:
        description: Delete failed
    """
    # check tồn tại
    exist = query_db(
        "SELECT id FROM Inventory WHERE id=?",
        (id,),
        one=True
    )

    if not exist:
        abort(404, "Inventory not found")

    # xóa
    success = execute_db(
        "DELETE FROM Inventory WHERE id=?",
        (id,)
    )

    if not success:
        abort(500, "Delete failed")

    return jsonify({
        "success": True,
        "message": "Deleted successfully"
    })
# ================= UPDATE =================
@inventory_bp.route('/update/<int:id>', methods=['PUT'])
def update_inventory(id):
    """
    Update inventory quantity
    ---
    tags:
      - Inventory
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID của inventory cần cập nhật
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - quantity
          properties:
            quantity:
              type: integer
              example: 150
    responses:
      200:
        description: Updated successfully
      400:
        description: Missing quantity
      500:
        description: Update failed
    """
    data = request.json

    if not data or "quantity" not in data:
        abort(400, "Missing quantity")

    success = execute_db(
        "UPDATE Inventory SET quantity=? WHERE id=?",
        (data['quantity'], id)
    )

    if not success:
        abort(500, "Update failed")

    return jsonify({"success": True, "message": "Updated successfully"})


# ================= SEARCH PRODUCT NAME =================
@inventory_bp.route('/search/product', methods=['GET'])
def search_product():
    """
        Search inventory by product name
        ---
        tags:
          - Inventory
        parameters:
          - in: query
            name: name
            type: string
            required: true
            description: Product name to search
            example: "Product A"
        responses:
          200:
            description: List of matched inventory
        """
    name = request.args.get("name")

    if not name:
        return jsonify({"success": True, "data": []})

    sql = """
        SELECT 
            i.id,
            w.name AS warehouse_name,
            p.name AS product_name,
            i.quantity
        FROM Inventory i
        JOIN Warehouses w ON i.warehouse_id = w.id
        JOIN Products p ON i.product_id = p.id
        WHERE p.name LIKE ?
    """

    data = query_db(sql, (f"%{name}%",))

    return jsonify({"success": True, "data": data})


# ================= SEARCH WAREHOUSE NAME =================
@inventory_bp.route('/search/warehouse', methods=['GET'])
def search_warehouse():
    """
       Search inventory by warehouse name
       ---
       tags:
         - Inventory
       parameters:
         - in: query
           name: name
           type: string
           required: true
           description: Warehouse name to search
           example: "Main Warehouse"
       responses:
         200:
           description: List of matched inventory
       """
    name = request.args.get("name")

    if not name:
        return jsonify({"success": True, "data": []})

    sql = """
        SELECT 
            i.id,
            w.name AS warehouse_name,
            p.name AS product_name,
            i.quantity
        FROM Inventory i
        JOIN Warehouses w ON i.warehouse_id = w.id
        JOIN Products p ON i.product_id = p.id
        WHERE w.name LIKE ?
    """

    data = query_db(sql, (f"%{name}%",))

    return jsonify({"success": True, "data": data})