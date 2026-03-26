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
    #Show all products from database
    products =  query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id');
    return jsonify(products),200

@inventory_bp.route('/products/<int:id>', methods=['GET'])
def get_product_id(id):
    """
    200 response with list of products
        category_name
        created_at
        description
        min_stock
        product_name
        sku
    """
    #Show products that have Id matches the search Id
    product_id = query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id where products.id = ?', (id,), one=True)
    return jsonify(product_id),200

@inventory_bp.route('/products/name=<name>', methods=['GET'])
def get_product_name(name):
    """
    200 response with list of products
        category_name
        created_at
        description
        min_stock
        product_name
        sku
    """
    #Show products that have Id matches the search Id
    name = name.strip()
    product_name = query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id where products.name like ?', ('%' +name + '%',))
    return jsonify(product_name),200

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
    # Receiving data in JSON file format
    data = request.get_json()
    sku = data.get('sku')
    name = data.get('product_name')
    category = data.get('category_name')
    min_stock = data.get('min_stock',0)
    description = data.get('description')

    if not all([sku, name, category, min_stock, description]):
        abort(400,description='Thông tin sản phẩm không được để trống')

    #Reformat data
    sku = str(sku).strip().upper()
    name = str(name).strip()
    category = str(category).strip()
    min_stock = int(min_stock)
    description = str(description).strip()

    exist_category = query_db('select id from Categories where name = ?', (category,), one=True)
    if exist_category is None:
        abort(400,description="Loại sản phẩm không tồn tại")
    category = exist_category['id']

    exist_sku = query_db('select id from Products where sku = ?', (sku,), one=True)
    if exist_sku:
        abort(400,description="Số định danh sản phẩm đã tồn tại")
    success = execute_db('insert into Products(sku,name,category_id,min_stock,description) '
                             'values (?,?,?,?,?)',(sku, name, category, min_stock, description))
    if success:
        return jsonify({'success': 'Thành công', 'message': "Sản phẩm đã được thêm vào"}), 200
    else:
        abort(500,description="Đã xảy ra lỗi khi thêm sản phẩm mới vào")

@inventory_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    """
    200 response with updated product with product_id:
        sku
        product_name
        category_name
        min_stock
        description
    """
    #Receiving data in JSON file format
    data = request.get_json()
    sku = data.get('sku')
    name = data.get('product_name')
    category = data.get('category_name')
    min_stock = data.get('min_stock')
    description = data.get('description')

    if not all([sku, name, category, min_stock, description]):
        abort(400, description='Thông tin sản phẩm không được để trống')

    #Reformat data
    sku = str(sku).strip().upper()
    name = str(name).strip()
    category = str(category).strip()
    min_stock = int(min_stock)
    description = str(description).strip()

    exist_product = query_db('select id from Products where id = ?', (id,), one=True)
    if exist_product is None:
        abort(400,description="Sản phẩm không tồn tại")

    exist_category = query_db('select id from Categories where name = ?', (category,), one=True)
    if exist_category is None:
        abort(400, description="Loại sản phẩm không tồn tại")
    category = exist_category['id']

    success = execute_db('UPDATE Products SET sku = ?, name = ?, category_id = ?, min_stock = ?, description = ? '
                         'WHERE id = ?', (sku,name, category,min_stock, description, id,))
    if success:
        return jsonify({'success': 'Thành công', 'message': 'THông tin sản phẩm đã đuọc cập nhật'}) , 200
    else:
        abort(500, description="Đã xảy ra lỗi khi cập nhật thông tin sản phẩm")