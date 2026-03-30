from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db

inventory_bp = Blueprint('inventory', __name__)

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
    data = get_inventory_by(
        request.args.get('warehouse_id', type=int),
        request.args.get('product_id', type=int)
    )

    return jsonify({
        "success": True,
        "data": data
    })


@inventory_bp.route('/inventory/add', methods=['POST'])
def add_inventory():
    data = request.json

    if not data:
        abort(400, "Invalid JSON")

    if not all(k in data for k in ("warehouse_id", "product_id", "quantity")):
        abort(400, "Missing fields")

    inventory = query_db(
        "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (data['warehouse_id'], data['product_id']),
        one=True
    )

    if not inventory:
        abort(404, "Inventory not found")

    # update inventory
    success = execute_db(
        """
        UPDATE Inventory
        SET quantity = quantity + ?
        WHERE warehouse_id = ? AND product_id = ?
        """,
        (data['quantity'], data['warehouse_id'], data['product_id'])
    )

    if not success:
        abort(500, "Update failed")

    execute_db(
        """
        INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type)
        VALUES (?, ?, ?, 'ADD')
        """,
        (data['product_id'], data['warehouse_id'], data['quantity'])
    )

    return jsonify({
        "success": True,
        "data": "Inventory added"
    })

@inventory_bp.route('/inventory/remove', methods=['POST'])
def remove_inventory():
    data = request.json

    if not data:
        abort(400, "Invalid JSON")

    if not all(k in data for k in ("warehouse_id", "product_id", "quantity")):
        abort(400, "Missing fields")

    inventory = query_db(
        "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
        (data['warehouse_id'], data['product_id']),
        one=True
    )

    if not inventory:
        abort(404, "Inventory not found")

    if inventory['quantity'] < data['quantity']:
        abort(400, "Not enough stock")

    # update inventory
    success = execute_db(
        """
        UPDATE Inventory
        SET quantity = quantity - ?
        WHERE warehouse_id = ? AND product_id = ?
        """,
        (data['quantity'], data['warehouse_id'], data['product_id'])
    )

    if not success:
        abort(500, "Update failed")

    execute_db(
        """
        INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type)
        VALUES (?, ?, ?, 'REMOVE')
        """,
        (data['product_id'], data['warehouse_id'], -data['quantity'])
    )

    return jsonify({
        "success": True,
        "data": "Inventory removed"
    })