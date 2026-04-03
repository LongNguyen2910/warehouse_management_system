from flask import Blueprint, jsonify, request, abort

import db_helper
from db_helper import query_db, execute_db
inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inbound', methods=['POST'])
def inbound():
    """
        API Tạo phiếu nhập sản phẩm và cập nhật kho
        ---
        tags:
          - Inventory
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - warehouse_name
                - staff_name
                - partner_name
                - items
              properties:
                warehouse_name:
                  type: string
                  example: "KHO QUẬN 1"
                staff_name:
                  type: string
                  example: "NGUYEN VAN A"
                partner_name:
                  type: string
                  example: "Công ty Nước giải khát ABC"
                items:
                  type: array
                  items:
                    type: object
                    required:
                      - product_name
                      - quantity
                      - price
                    properties:
                      product_name:
                        type: string
                        example: "Pepsi Lon 330ml"
                      quantity:
                        type: integer
                        example: 100
                      price:
                        type: number
                        example: 5000.50
        responses:
          200:
            description: Đã thêm thông tin phiếu nhập thành công
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
          400:
            description: Dữ liệu không hợp lệ (Tên kho, nhân viên hoặc sản phẩm không tồn tại)
          500:
            description: Lỗi hệ thống khi ghi dữ liệu vào cơ sở dữ liệu
        """
    data = request.get_json()
    warehouse = data.get('warehouse_name')
    staff = data.get('staff_name')
    partner = data.get('partner_name')
    items = data.get('items')

    # Validate data
    if not all([warehouse, staff, partner, items]):
        abort(400, description="Thông tin phiếu nhập không được để trống")

    warehouse = str(warehouse).strip().upper()
    staff = str(staff).strip().upper()
    partner = str(partner).strip()

    exist_warehouse = query_db("SELECT id FROM warehouses WHERE name = ?", (warehouse,), one=True)
    if exist_warehouse is None:
        abort(400, description="Tên nhà kho không tồn tại")
    warehouse = exist_warehouse["id"]

    exist_staff = query_db("SELECT id FROM Users WHERE username = ?", (staff,), one=True)
    if exist_staff is None:
        abort(400, description="Nhân viên không tồn tại")
    staff = exist_staff["id"]

    products = [item['product_name'] for item in items]
    placeholders = ','.join(['?'] * len(products))
    check_product = query_db(
        f"SELECT name FROM Products WHERE name IN ({placeholders})",
        tuple(products)
    )
    exist_product = [row["name"] for row in check_product]
    for product in products:
        if product not in exist_product:
            abort(400, description=f"Sản phẩm {product} không tồn tại. Hãy tạo mới")

        # Create inbound receipt
    success = query_db(
    "INSERT INTO Receipts (type, warehouse_id, staff_id, partner_name) OUTPUT INSERTED.id VALUES (N'INBOUND',?,?,?)",
        (warehouse, staff, partner), one=True
    )
    if not success:
        abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

    receipt = success["id"]

    for item in items:
        name = item['product_name']
        quantity = item['quantity']
        price = item['price']

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        success = execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) VALUES (?,?,?,?)",
            (receipt, product_id, quantity, price)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

        exist_inventory = query_db(
            "SELECT id FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse, product_id), one=True
        )
        if exist_inventory is None:
            success = execute_db(
                 "INSERT INTO Inventory (warehouse_id, product_id, quantity) VALUES (?,?,?)",
                (warehouse, product_id, quantity)
            )
            if not success:
                    abort(500, description="Đã xảy ra lỗi khi thêm sản phẩm vào kho")
        else:
            success = execute_db(
            "UPDATE Inventory SET quantity = quantity + ? WHERE id = ?",
            (int(quantity), exist_inventory["id"])
            )
            if not success:
                abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

        success = execute_db(
            "INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type, reference_id) VALUES (?,?,?,N'INBOUND',?)",
            (product_id, warehouse, int(quantity), receipt)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu nhập thành công"}), 200

@inventory_bp.route('/outbound', methods=['POST'])
def outbound():
    """
        API Tạo phiếu xuất sản phẩm và cập nhật kho
        ---
        tags:
          - Inventory
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - warehouse_name
                - staff_name
                - partner_name
                - items
              properties:
                warehouse_name:
                  type: string
                  example: "KHO QUẬN 1"
                staff_name:
                  type: string
                  example: "NGUYEN VAN A"
                partner_name:
                  type: string
                  example: "Công ty Nước giải khát ABC"
                items:
                  type: array
                  items:
                    type: object
                    required:
                      - product_name
                      - quantity
                      - price
                    properties:
                      product_name:
                        type: string
                        example: "Pepsi Lon 330ml"
                      quantity:
                        type: integer
                        example: 100
                      price:
                        type: number
                        example: 5000.50
        responses:
          200:
            description: Đã thêm thông tin phiếu xuất thành công
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
          400:
            description: Dữ liệu không hợp lệ (Tên kho, nhân viên, sản phẩm không tồn tại hoặc không đủ số lượng)
          500:
            description: Lỗi hệ thống khi ghi dữ liệu vào cơ sở dữ liệu
        """
    data = request.get_json()
    warehouse = data.get('warehouse_name')
    staff = data.get('staff_name')
    partner = data.get('partner_name')
    items = data.get('items')

    # Validate data
    if not all([warehouse, staff, partner, items]):
        abort(400, description="Thông tin phiếu xuất không được để trống")

    warehouse = str(warehouse).strip().upper()
    staff = str(staff).strip().upper()
    partner = str(partner).strip()

    exist_warehouse = query_db("SELECT id FROM warehouses WHERE name = ?", (warehouse,), one=True)
    if exist_warehouse is None:
        abort(400, description="Tên nhà kho không tồn tại")
    warehouse = exist_warehouse["id"]

    exist_staff = query_db("SELECT id FROM Users WHERE username = ?", (staff,), one=True)
    if exist_staff is None:
        abort(400, description="Nhân viên không tồn tại")
    staff = exist_staff["id"]

    # Kiểm tra sản phẩm tồn tại
    products = [item['product_name'] for item in items]
    placeholders = ','.join(['?'] * len(products))
    check_product = query_db(
        f"SELECT name FROM Products WHERE name IN ({placeholders})",
        tuple(products)
    )
    exist_product = [row["name"] for row in check_product]
    for product in products:
        if product not in exist_product:
            abort(400, description=f"Sản phẩm {product} không tồn tại")

    # Kiểm tra số lượng tồn kho trước khi xuất (outbound khác inbound ở bước này)
    for item in items:
        name = item['product_name']
        quantity = item['quantity']

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        inventory = query_db(
            "SELECT id, quantity FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse, product_id), one=True
        )
        if inventory is None:
            abort(400, description=f"Sản phẩm {name} không có trong kho")
        if inventory["quantity"] < quantity:
            abort(400,
                  description=f"Sản phẩm {name} không đủ số lượng. Tồn kho: {inventory['quantity']}, yêu cầu: {quantity}")

    # Tạo phiếu xuất
    success = query_db(
        "INSERT INTO Receipts (type, warehouse_id, staff_id, partner_name) OUTPUT INSERTED.id VALUES (N'OUTBOUND',?,?,?)",
        (warehouse, staff, partner), one=True
    )
    if not success:
        abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

    receipt = success["id"]

    for item in items:
        name = item['product_name']
        quantity = item['quantity']
        price = item['price']

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        # Thêm chi tiết phiếu xuất
        success = execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) VALUES (?,?,?,?)",
            (receipt, product_id, quantity, price)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

        # Trừ số lượng tồn kho (outbound thì trừ, inbound thì cộng)
        inventory = query_db(
            "SELECT id FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse, product_id), one=True
        )
        success = execute_db(
            "UPDATE Inventory SET quantity = quantity - ? WHERE id = ?",
            (int(quantity), inventory["id"])
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

        # Ghi log
        success = execute_db(
            "INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type, reference_id) VALUES (?,?,?,N'OUTBOUND',?)",
            (product_id, warehouse, int(quantity), receipt)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu xuất thành công"}), 200

@inventory_bp.route("/", methods=["GET"])
def get_inventory():
    """
        API Lấy danh sách toàn bộ phiếu kèm chi tiết hàng hóa
        ---
        tags:
          - Inventory
        responses:
          200:
            description: Danh sách các phiếu đã được nhóm theo ID
            schema:
              type: array
              items:
                type: object
                properties:
                  id: {type: integer}
                  type: {type: string}
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        product_name: {type: string}
                        quantity: {type: integer}
        """

    sql = """
          SELECT r.id       as receipt_id, \
                 r.type, \
                 r.partner_name, \
                 r.created_at, \
                 w.name     as warehouse_name, \
                 u.username as staff_name, \
                 p.name     as product_name, \
                 p.sku, \
                 rd.quantity, \
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          ORDER BY r.created_at DESC \
          """

    raw_data = query_db(sql)

    receipts_dict = {}

    for row in raw_data:
        r_id = row['receipt_id']

        if r_id not in receipts_dict:
            receipts_dict[r_id] = {
                "id": r_id,
                "type": row['type'],
                "warehouse_name": row['warehouse_name'],
                "staff_name": row['staff_name'],
                "partner_name": row['partner_name'],
                "created_at": row['created_at'],
                "items": []
            }

        receipts_dict[r_id]['items'].append({
            "product_name": row['product_name'],
            "sku": row['sku'],
            "quantity": row['quantity'],
            "price": row['price'],
            "total_price": row['quantity'] * row['price']
        })

    # 3. Chuyển từ Dictionary sang List để trả về JSON
    final_result = list(receipts_dict.values())

    return jsonify(final_result), 200


@inventory_bp.route('/<int:id>', methods=['GET'])
def get_receipt_by_id(id):
    """
        API Lấy chi tiết một phiếu bất kỳ theo ID
        ---
        tags:
          - Inventory
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID của phiếu nhập hoặc xuất
        responses:
          200:
            description: Thông tin chi tiết của phiếu tìm thấy
            schema:
              type: object
              properties:
                id: {type: integer}
                type: {type: string}
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      product: {type: string}
                      qty: {type: integer}
          404:
            description: Không tìm thấy ID phiếu này trong hệ thống
        """
    sql = """
          SELECT r.id, \
                 r.type, \
                 r.partner_name, \
                 r.created_at,
                 w.name     as warehouse_name, \
                 u.username as staff_name,
                 p.name     as product_name, \
                 p.sku, \
                 rd.quantity, \
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.id = ? \
          """
    rows = query_db(sql, (id,))

    if not rows:
        abort(404, description="Không tìm thấy phiếu")

    # Dùng Dict để gom: Vì chỉ có 1 ID nên ta chỉ cần 1 biến dict duy nhất
    receipt = {
        "id": rows[0]['id'],
        "type": rows[0]['type'],
        "warehouse": rows[0]['warehouse_name'],
        "staff": rows[0]['staff_name'],
        "partner": rows[0]['partner_name'],
        "items": []  # Đây là nơi chứa danh sách sản phẩm
    }

    for row in rows:
        receipt['items'].append({
            "product": row['product_name'],
            "qty": row['quantity'],
            "price": row['price']
        })

    # Ở đây không cần .values() vì ta chỉ trả về 1 Object {}, không phải 1 mảng []
    return jsonify(receipt), 200


@inventory_bp.route('/inbound', methods=['GET'])
def get_inbound_receipts():
    """
        API Lấy danh sách toàn bộ Phiếu Nhập kèm chi tiết hàng hóa
        ---
        tags:
          - Inventory
        responses:
          200:
            description: Danh sách các phiếu nhập hiện có trong hệ thống
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 10
                  warehouse:
                    type: string
                    example: "Kho Tổng A"
                  staff:
                    type: string
                    example: "admin_tung"
                  partner:
                    type: string
                    example: "Công ty PepsiCo"
                  created_at:
                    type: string
                    example: "2024-03-20 14:30:00"
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        product:
                          type: string
                          example: "Pepsi Lon 330ml"
                        sku:
                          type: string
                          example: "P001"
                        qty:
                          type: integer
                          example: 50
                        price:
                          type: number
                          example: 5500.0
        """
    # 1. SQL JOIN lấy tất cả thông tin liên quan, lọc theo INBOUND
    sql = """
          SELECT r.id       as receipt_id, \
                 r.partner_name, \
                 r.created_at, \
                 w.name     as warehouse_name, \
                 u.username as staff_name, \
                 p.name     as product_name, \
                 p.sku, \
                 rd.quantity, \
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.type = 'INBOUND'
          ORDER BY r.created_at DESC \
          """
    raw_data = query_db(sql)

    # 2. Dùng Dictionary để nhóm sản phẩm vào từng Phiếu Nhập
    inbound_dict = {}

    for row in raw_data:
        rid = row['receipt_id']
        if rid not in inbound_dict:
            inbound_dict[rid] = {
                "id": rid,
                "warehouse": row['warehouse_name'],
                "staff": row['staff_name'],
                "partner": row['partner_name'],
                "created_at": row['created_at'],
                "items": []  # Danh sách sản phẩm của phiếu này
            }

        # Thêm sản phẩm vào mảng items của phiếu tương ứng
        inbound_dict[rid]['items'].append({
            "product": row['product_name'],
            "sku": row['sku'],
            "qty": row['quantity'],
            "price": row['price']
        })

    # 3. Trả về phần Giá trị (List các phiếu) cho jsonify
    # jsonify tự biết lấy các Key (id, warehouse, items...) để tạo JSON Object
    return jsonify(list(inbound_dict.values())), 200


@inventory_bp.route('/outbound', methods=['GET'])
def get_outbound_receipts():
    """
        API Lấy danh sách toàn bộ Phiếu Xuất kèm chi tiết hàng hóa
        ---
        tags:
          - Inventory
        responses:
          200:
            description: Danh sách các phiếu xuất (Outbound)
            schema:
              type: array
              items:
                type: object
                properties:
                  id: {type: integer}
                  warehouse: {type: string}
                  customer: {type: string}
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        product: {type: string}
                        qty: {type: integer}
                        total: {type: number}
        """
    sql = """
          SELECT r.id, \
                 r.partner_name, \
                 r.created_at, \
                 w.name     as warehouse_name, \
                 u.username as staff_name, \
                 p.name     as product_name, \
                 p.sku, \
                 rd.quantity, \
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.type = 'OUTBOUND'
          ORDER BY r.created_at DESC \
          """
    raw_data = query_db(sql)

    # Gom nhóm bằng Dictionary
    outbound_dict = {}
    for row in raw_data:
        rid = row['id']
        if rid not in outbound_dict:
            outbound_dict[rid] = {
                "id": rid,
                "warehouse": row['warehouse_name'],
                "staff": row['staff_name'],
                "customer": row['partner_name'],  # Đối với phiếu xuất, partner là khách hàng
                "created_at": row['created_at'],
                "items": []
            }

        outbound_dict[rid]['items'].append({
            "product": row['product_name'],
            "sku": row['sku'],
            "qty": row['quantity'],
            "price": row['price'],
            "total": row['quantity'] * row['price']
        })

    # Chuyển Dictionary Values thành List để jsonify tạo mảng []
    return jsonify(list(outbound_dict.values())), 200

@inventory_bp.route('/<int:id>', methods=['DELETE'])
def delete_receipt(id):
    """
    API Xóa hoàn toàn thông tin một phiếu nhập hoặc xuất
    ---
    tags:
      - Inventory
    summary: Xóa phiếu nhập/xuất theo ID
    parameters:
      - name: id
        in: path
        required: true
        description: ID của phiếu cần xóa (Chi tiết phiếu sẽ bị xóa theo do CASCADE)
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Xóa phiếu thành công
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Xóa thông tin phiếu thành công"
      404:
        description: Không tìm thấy phiếu với ID đã cho
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: "Thông tin phiếu không tồn tại"
      500:
        description: Lỗi máy chủ khi thực hiện xóa
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: "Đã có lỗi khi xóa thông tin phiếu"
    """

    exist_receipt = query_db("SELECT id FROM Receipts WHERE id = ?", (id,), one=True)
    if exist_receipt is None:
        return jsonify({"success": False, "message" : "Thông tin phiếu không tồn tại"}) ,404
    success = query_db("DELETE FROM Receipts WHERE id = ?", (id,))
    if success:
        return jsonify({"success" : True, "message" : "Xóa thông tin phiếu thành công "}) , 200
    else:
        return jsonify({"success" : False, "message" : "Đã có lỗi khi xóa thông tin phiếu"}), 500
