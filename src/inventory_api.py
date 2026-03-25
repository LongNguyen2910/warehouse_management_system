from flask import Blueprint, jsonify, request, abort

import db_helper
from db_helper import query_db, execute_db
inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/products', methods=['GET'])
def get_products():

    """
    200 response with list of products
        category_name
        created_at
        description
        min_stock
        product_name
        sku
    """

    products =  query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id');
    return jsonify(products)

@inventory_bp.route('/products', methods=['POST'])
def create_product():
    """
    200 response with new product:
        sku
        product_name
        category_name
        min_stock
        description
    """
    data = request.get_json()
    sku = data.get('sku')
    name = data.get('product_name')
    category = data.get('category_name')
    min_stock = data.get('min_stock',0)
    description = data.get('description')
    if not all([sku, name, category, min_stock, description]):
        abort(400,description='Thông tin sản phẩm không được để trống')
    sku = str(sku).strip().upper()
    name = str(name).strip()
    category = str(category).strip()
    min_stock = int(min_stock)
    description = str(description).strip()
    exist_category = query_db('select id from Categories where name = ?', [category], one=True)
    if exist_category is None:
        abort(400,description="Loại sản phẩm không tồn tại")
    category = exist_category['id']
    exist_sku = query_db('select id from Products where sku = ?', [sku], one=True)
    if exist_sku:
        abort(400,description="Số định danh sản phẩm đã tồn tại")
    add_product = execute_db('insert into Products(sku,name,category_id,min_stock,description) '
                             'values (?,?,?,?,?)',(sku, name, category, min_stock, description))
    if add_product:
        return jsonify({'success': True, 'message': "Sản phẩm đã được thêm vào"}), 200
    else:
        abort(500,description="Đã xảy ra lỗi khi thêm sản phẩm mới vào")

