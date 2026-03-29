from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db

inventory_bp = Blueprint('inventory', __name__)
# helper
def get_inventory_by(warehouse_id=None, product_id=None):
    query = "SELECT * FROM Inventory WHERE 1=1"
    params = []

    if warehouse_id is not None:
        query += " AND warehouse_id=?"
        params.append(warehouse_id)

    if product_id is not None:
        query += " AND product_id=?"
        params.append(product_id)

    return query_db(query, tuple(params))
@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    """
    Get inventory (filter by warehouse_id, product_id)
    ---
    tags:
      - Inventory
    parameters:
      - in: query
        name: warehouse_id
        type: integer
      - in: query
        name: product_id
        type: integer
    responses:
      200:
        description: List of inventory
      404:
        description: No data found
    """

    warehouse_id = request.args.get('warehouse_id', type=int)
    product_id = request.args.get('product_id', type=int)

    data = get_inventory_by(warehouse_id, product_id)

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
    inventory = query_db(
        "SELECT * FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (data['warehouse_id'], data['product_id']),
        one=True
    )

    if not inventory:
        abort(404, "Inventory not found")

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
    inventory = query_db(
        "SELECT * FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (data['warehouse_id'], data['product_id']),
        one=True
    )

    if not inventory:
        abort(404, "Inventory not found")

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
