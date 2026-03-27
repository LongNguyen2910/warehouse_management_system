from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db

inventory_bp = Blueprint('inventory', __name__)
@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    """
    Get all inventory
    ---
    tags:
      - Inventory
    responses:
        200:
          description: List of inventory
        500:
          description: Database error
    """
    data = query_db("SELECT * FROM Inventory")

    return jsonify({
        "success": True,
        "data": data
    })
@inventory_bp.route('/inventory/<int:warehouse_id>', methods=['GET'])
def get_inventory_by_warehouse(warehouse_id):
    """
    Get inventory by warehouse
    ---
    tags:
      - Inventory
    parameters:
      - in: path
        name: warehouse_id
        type: integer
        required: true
    responses:
      200:
        description: Inventory list
      404:
        description: No data found
    """

    data = query_db(
        "SELECT * FROM Inventory WHERE warehouse_id=?",
        (warehouse_id,)
    )

    if not data:
        abort(404, "No inventory found")

    return jsonify({
        "success": True,
        "data": data
    })
# xem 1 sản phẩm
@inventory_bp.route('/inventory/product/<int:product_id>', methods=['GET'])
def get_product_inventory(product_id):
    """
    Get inventory by product
    ---
    tags:
      - Inventory
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Inventory list
      404:
        description: Not found
    """

    data = query_db(
        "SELECT * FROM Inventory WHERE product_id=?",
        (product_id,)
    )

    if not data:
        abort(404, "No data found")

    return jsonify({
        "success": True,
        "data": data
    })
@inventory_bp.route('/inventory/add', methods=['POST'])
def add_inventory():
    """
    Add inventory
    ---
    tags:
      - Inventory
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - warehouse_id
            - product_id
            - quantity
          properties:
            warehouse_id:
              type: integer
            product_id:
              type: integer
            quantity:
              type: integer
    responses:
      200:
        description: Inventory added
      400:
        description: Invalid input
      500:
        description: Update failed
    """

    data = request.json

    if not data:
        abort(400, "Invalid JSON")

    if not all(k in data for k in ("warehouse_id", "product_id", "quantity")):
        abort(400, "Missing fields")

    success = execute_db(
        """
        UPDATE Inventory
        SET quantity = quantity + ?
        WHERE warehouse_id = ?
          AND product_id = ?
        """,
        (data['quantity'], data['warehouse_id'], data['product_id'])
    )

    if not success:
        abort(500, "Update failed")

    return jsonify({
        "success": True,
        "data": "Inventory added"
    })
@inventory_bp.route('/inventory/remove', methods=['POST'])
def remove_inventory():
    """
    Remove inventory
    ---
    tags:
      - Inventory
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - warehouse_id
            - product_id
            - quantity
          properties:
            warehouse_id:
              type: integer
            product_id:
              type: integer
            quantity:
              type: integer
    responses:
      200:
        description: Inventory removed
      400:
        description: Not enough stock
      500:
        description: Update failed
    """

    data = request.json

    if not data:
        abort(400, "Invalid JSON")

    if not all(k in data for k in ("warehouse_id", "product_id", "quantity")):
        abort(400, "Missing fields")

    stock = query_db(
        "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (data['warehouse_id'], data['product_id']),
        one=True
    )

    if not stock or stock['quantity'] < data['quantity']:
        abort(400, "Not enough stock")

    success = execute_db(
        """
        UPDATE Inventory
        SET quantity = quantity - ?
        WHERE warehouse_id = ?
          AND product_id = ?
        """,
        (data['quantity'], data['warehouse_id'], data['product_id'])
    )

    if not success:
        abort(500, "Update failed")

    return jsonify({
        "success": True,
        "data": "Inventory removed"
    })
