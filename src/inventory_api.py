from flask import Blueprint, jsonify
import db_helper
inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/products', methods=['GET'])
def get_products():
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sku, name FROM products")

    rows = cursor.fetchall()
    products = []
    for row in rows:
        products.append({
            'id': row.id,
            'sku': row.sku,
            'name': row.name
        })
    conn.close()
    return jsonify(products)

