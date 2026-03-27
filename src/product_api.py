from flask import Blueprint, jsonify, request, abort

import db_helper
from db_helper import query_db, execute_db
products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
def get_products():
    """
    API Lấy danh sách các sản phẩm có trong hệ thống
    ---
    tags:
      - Products
    responses:
      200:
        description: Danh sách các sản phẩm hiện có
        schema:
          type: array
          items:
            properties:
              sku:
                type: string
              product_name:
                type: string
              category_name:
                type: string
              min_stock:
                type: integer
              description:
                type: string
              created_at:
                 type: string
    """
    #Show all products from database
    products =  query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id');
    return jsonify(products),200

@products_bp.route('/<id>', methods=['GET'])
def get_product_id(id):
    """
        API Lấy thông tin sản phẩm theo ID
        ---
        tags:
          - Products
        parameters:
          - name: id
            in: path
            required: true
            type: integer
        responses:
          200:
            description: Thông tin sản phẩm
            schema:
              type: object
              properties:
                sku:
                    type: string
                product_name:
                    type: string
                category_name:
                    type: string
                min_stock:
                    type: integer
                description:
                    type: string
                created_at:
                    type: string
          404:
            description: sản phẩm không tìm thấy hoặc không tồn tại
        """
    #Show products that have Id matches the search Id
    product_id = query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id where products.id = ?', (id,), one=True)
    return jsonify(product_id),200

@products_bp.route('/name=<name>', methods=['GET'])
def get_product_name(name):
    """
        API Lấy thông tin sản phẩm theo ID
        ---
        tags:
          - Products
        parameters:
          - name: name
            in: path
            required: true
            type: string
        responses:
          200:
            description: Thông tin sản phẩm
            schema:
              type: object
              properties:
                sku:
                    type: string
                product_name:
                    type: string
                category_name:
                    type: string
                min_stock:
                    type: integer
                description:
                    type: string
                created_at:
                    type: string
          404:
            description: sản phẩm không tìm thấy hoặc không tồn tại
        """
    #Show products that have product name matches the search name
    name = name.strip()
    product_name = query_db('select sku, products.name as product_name, min_stock, description, created_at, categories.name as category_name '
                         'from products join Categories on Categories.id = products.category_id where products.name like ?', ('%' +name + '%',))
    return jsonify(product_name),200

@products_bp.route('/', methods=['POST'])
def add_product():
    """
        API Thêm sản phẩm mới
        ---
        tags:
          - Products
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                sku:
                    type: string
                product_name:
                    type: string
                category_name:
                    type: string
                min_stock:
                    type: integer
                description:
                    type: string
                created_at:
                    type: string
        responses:
          200:
            description: Thêm thành công
          400:
            description: Dữ liệu không hợp lệ
          500:
            description: "Đã xảy ra lỗi khi thêm sản phẩm mới"
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
    exist_product = query_db('select id from Products where name = ?', (name,), one=True)
    if exist_product:
        abort(400, description="Sản phẩm đã tồn tại")
    success = execute_db('insert into Products(sku,name,category_id,min_stock,description) '
                             'values (?,?,?,?,?)',(sku, name, category, min_stock, description))
    if success:
        return jsonify({'success': 'Thành công', 'message': "Sản phẩm đã được thêm vào"}), 200
    else:
        abort(500,description="Đã xảy ra lỗi khi thêm sản phẩm mới vào")

@products_bp.route('/<id>', methods=['PUT'])
def update_product(id):
    """
        API sửa thông tin sản phẩm
        ---
        tags:
          - Products
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                sku:
                    type: string
                product_name:
                    type: string
                category_name:
                    type: string
                min_stock:
                    type: integer
                description:
                    type: string
                created_at:
                    type: string
        responses:
          200:
            description: sửa thông tin thành công
          400:
            description: Dữ liệu không hợp lệ
          500:
            description: "Đã xảy ra lỗi khi sửa thông tin sản phẩm"
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

@products_bp.route('/<id>', methods=['DELETE'])
def delete_product(id):
    """
        API Xóa thông tin sản phẩm
        ---
        tags:
          - Products
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID của sản phẩm cần xóa
        responses:
          200:
            description: Xóa sản phẩm thành công
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Thông tin sản phẩm đã được xóa"
          400:
            description: Không thể xóa do sản phẩm không tồn tại hoặc có dữ liệu ràng buộc ở bảng khác
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Không thể xóa sản phẩm vì còn dữ liệu trong bảng khác"
                table_to_clean:
                  type: array
                  items:
                    type: string
                  example: ["Nhật ký Kho (Inventory_Logs)", "Kho (Inventory)"]
          500:
            description: "Đã xảy ra lỗi hệ thống khi xóa thông tin sản phẩm"
        """
    exist_product = query_db('select id from Products where id = ?', (id,), one=True)
    if exist_product is None:
        abort(400, description="Sản phẩm không tồn tại")

    #Check product's infomation in other tables
    dependencies = []
    exist_logs = query_db('select * from Inventory_Logs where product_id = ?', (id,), one=True)
    if exist_logs:
        dependencies.append("Nhật ký Kho (Inventory_Logs)")
    exist_inventory = query_db('select * from Inventory where product_id = ?', (id,), one=True)
    if exist_inventory:
        dependencies.append("Kho (Inventory)")
    exist_receipt = query_db('select * from Receipt_Details where product_id = ?', (id,), one=True)
    if exist_receipt:
        dependencies.append("Chi tiết yêu cầu (Receipt_Details)")
    exist_transfer = query_db('select * from Transfer_Details where product_id = ?', (id,), one=True)
    if exist_transfer:
        dependencies.append("Chi tiết giao hàng (Transfer_Details)")
    if dependencies:
        return jsonify({'message': f"Không thể xóa sản phẩm vì còn dữ liệu trong bảng khác", 'table_to_clean': dependencies}), 400

    success = execute_db('DELETE FROM Products WHERE id = ?', (id,))
    if success:
        return jsonify({'success': True, 'message': 'Thông tin sản phẩm đã được xóa'}) ,200
    else:
        abort(500, description="Đã xảy ra lỗi khi xóa thông tin sản phẩm")