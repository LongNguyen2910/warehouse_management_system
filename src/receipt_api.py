from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import get_jwt, jwt_required

import db_helper
from db_helper import query_db, execute_db
receipt_bp = Blueprint('receipts', __name__)

@receipt_bp.route('/inbound', methods=['POST'])
@jwt_required()
def inbound():
    """
        API Tạo phiếu nhập sản phẩm và cập nhật kho
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"
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
    warehouse_id = exist_warehouse["id"]  # FIX: dùng biến mới tránh ghi đè

    exist_staff = query_db("SELECT id FROM Users WHERE username = ?", (staff,), one=True)
    if exist_staff is None:
        abort(400, description="Nhân viên không tồn tại")
    staff_id = exist_staff["id"]  # FIX: dùng biến mới tránh ghi đè

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

    # FIX: CREATE RECEIPT nằm NGOÀI vòng for (trước đây bị indent lệch vào trong)
    success = query_db(
        "INSERT INTO Receipts (type, warehouse_id, staff_id, partner_name) OUTPUT INSERTED.id VALUES (N'INBOUND',?,?,?)",
        (warehouse_id, staff_id, partner), one=True
    )
    if not success:
        abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

    receipt_id = success["id"]  # FIX: dùng biến mới tránh ghi đè biến success

    for item in items:
        name = item['product_name']
        quantity = int(item['quantity'])
        price = item['price']

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        success = execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) VALUES (?,?,?,?)",
            (receipt_id, product_id, quantity, price)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

        exist_inventory = query_db(
            "SELECT id FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse_id, product_id), one=True
        )
        if exist_inventory is None:
            success = execute_db(
                "INSERT INTO Inventory (warehouse_id, product_id, quantity) VALUES (?,?,?)",
                (warehouse_id, product_id, quantity)
            )
            if not success:
                abort(500, description="Đã xảy ra lỗi khi thêm sản phẩm vào kho")
        else:
            success = execute_db(
                "UPDATE Inventory SET quantity = quantity + ? WHERE id = ?",
                (quantity, exist_inventory['id'])  # FIX: dùng ['id'] thay vì [0]
            )
            if not success:
                abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

        success = execute_db(
            "INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type, reference_id) VALUES (?,?,?,N'INBOUND',?)",
            (product_id, warehouse_id, quantity, receipt_id)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu nhập thành công"}), 200


@receipt_bp.route('/outbound', methods=['POST'])
@jwt_required()
def outbound():
    """
        API Tạo phiếu xuất sản phẩm và cập nhật kho
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"
          500:
            description: Lỗi hệ thống khi ghi dữ liệu vào cơ sở dữ liệu
        """
    data = request.get_json()
    warehouse = data.get('warehouse_name')
    staff = data.get('staff_name')
    partner = data.get('partner_name')
    items = data.get('items')

    if not all([warehouse, staff, partner, items]):
        abort(400, description="Thông tin phiếu xuất không được để trống")

    warehouse = str(warehouse).strip().upper()
    staff = str(staff).strip().upper()
    partner = str(partner).strip()

    exist_warehouse = query_db("SELECT id FROM warehouses WHERE name = ?", (warehouse,), one=True)
    if exist_warehouse is None:
        abort(400, description="Tên nhà kho không tồn tại")
    warehouse_id = exist_warehouse["id"]  # FIX: biến riêng

    exist_staff = query_db("SELECT id FROM Users WHERE username = ?", (staff,), one=True)
    if exist_staff is None:
        abort(400, description="Nhân viên không tồn tại")
    staff_id = exist_staff["id"]  # FIX: biến riêng

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

    # Kiểm tra số lượng tồn kho trước khi xuất
    for item in items:
        name = item['product_name']
        quantity = int(item['quantity'])

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        inventory = query_db(
            "SELECT id, quantity FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse_id, product_id), one=True
        )
        if inventory is None:
            abort(400, description=f"Sản phẩm {name} không có trong kho")
        if inventory["quantity"] < quantity:
            abort(400, description=f"Sản phẩm {name} không đủ số lượng. Tồn kho: {inventory['quantity']}, yêu cầu: {quantity}")

    # Tạo phiếu xuất
    success = query_db(
        "INSERT INTO Receipts (type, warehouse_id, staff_id, partner_name) OUTPUT INSERTED.id VALUES (N'OUTBOUND',?,?,?)",
        (warehouse_id, staff_id, partner), one=True
    )
    if not success:
        abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

    receipt_id = success["id"]

    for item in items:
        name = item['product_name']
        quantity = int(item['quantity'])
        price = item['price']

        product_id = query_db("SELECT id FROM Products WHERE name = ?", (name,), one=True)["id"]

        success = execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) VALUES (?,?,?,?)",
            (receipt_id, product_id, quantity, price)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

        inventory = query_db(
            "SELECT id FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse_id, product_id), one=True
        )
        success = execute_db(
            "UPDATE Inventory SET quantity = quantity - ? WHERE id = ?",
            (quantity, inventory["id"])
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

        success = execute_db(
            "INSERT INTO Inventory_Logs (product_id, warehouse_id, change_amount, action_type, reference_id) VALUES (?,?,?,N'OUTBOUND',?)",
            (product_id, warehouse_id, quantity, receipt_id)
        )
        if not success:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu xuất thành công"}), 200


@receipt_bp.route("/", methods=["GET"])
@jwt_required()
def get_inventory():
    """
        API Lấy danh sách toàn bộ phiếu kèm chi tiết hàng hóa
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"  
        """
    sql = """
          SELECT r.id       as receipt_id,
                 r.type,
                 r.partner_name,
                 r.created_at,
                 w.name     as warehouse_name,
                 u.username as staff_name,
                 p.name     as product_name,
                 p.sku,
                 rd.quantity,
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          ORDER BY r.created_at DESC
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
                "created_at": str(row['created_at']),
                "items": []
            }
        receipts_dict[r_id]['items'].append({
            "product_name": row['product_name'],
            "sku": row['sku'],
            "quantity": row['quantity'],
            "price": row['price'],
            "total_price": row['quantity'] * row['price']
        })

    return jsonify(list(receipts_dict.values())), 200


@receipt_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_receipt_by_id(id):
    """
        API Lấy chi tiết một phiếu bất kỳ theo ID
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"
          404:
            description: Không tìm thấy ID phiếu này trong hệ thống
        """
    sql = """
          SELECT r.id,
                 r.type,
                 r.partner_name,
                 r.created_at,
                 w.name     as warehouse_name,
                 u.username as staff_name,
                 p.name     as product_name,
                 p.sku,
                 rd.quantity,
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.id = ?
          """
    rows = query_db(sql, (id,))
    if not rows:
        abort(404, description="Không tìm thấy phiếu")

    receipt = {
        "id": rows[0]['id'],
        "type": rows[0]['type'],
        "warehouse": rows[0]['warehouse_name'],
        "staff": rows[0]['staff_name'],
        "partner": rows[0]['partner_name'],
        "created_at": str(rows[0]['created_at']),
        "items": []
    }
    for row in rows:
        receipt['items'].append({
            "product": row['product_name'],
            "sku": row['sku'],
            "qty": row['quantity'],
            "price": row['price']
        })

    return jsonify(receipt), 200


@receipt_bp.route('/inbound', methods=['GET'])
@jwt_required()
def get_inbound_receipts():
    """
        API Lấy danh sách toàn bộ Phiếu Nhập kèm chi tiết hàng hóa
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"
        """
    sql = """
          SELECT r.id       as receipt_id,
                 r.partner_name,
                 r.created_at,
                 w.name     as warehouse_name,
                 u.username as staff_name,
                 p.name     as product_name,
                 p.sku,
                 rd.quantity,
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.type = 'INBOUND'
          ORDER BY r.created_at DESC
          """
    raw_data = query_db(sql)
    inbound_dict = {}

    for row in raw_data:
        rid = row['receipt_id']
        if rid not in inbound_dict:
            inbound_dict[rid] = {
                "id": rid,
                "warehouse": row['warehouse_name'],
                "staff": row['staff_name'],
                "partner": row['partner_name'],
                "created_at": str(row['created_at']),
                "items": []
            }
        inbound_dict[rid]['items'].append({
            "product": row['product_name'],
            "sku": row['sku'],
            "qty": row['quantity'],
            "price": row['price']
        })

    return jsonify(list(inbound_dict.values())), 200


@receipt_bp.route('/outbound', methods=['GET'])
@jwt_required()
def get_outbound_receipts():
    """
        API Lấy danh sách toàn bộ Phiếu Xuất kèm chi tiết hàng hóa
        ---
        tags:
          - Receipt
        security:
          - Bearer: []
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
          401:
            description: "Chưa xác thực hoặc token không hợp lệ"
        """
    sql = """
          SELECT r.id,
                 r.partner_name,
                 r.created_at,
                 w.name     as warehouse_name,
                 u.username as staff_name,
                 p.name     as product_name,
                 p.sku,
                 rd.quantity,
                 rd.price
          FROM Receipts r
                   JOIN Warehouses w ON r.warehouse_id = w.id
                   JOIN Users u ON r.staff_id = u.id
                   JOIN Receipt_Details rd ON r.id = rd.receipt_id
                   JOIN Products p ON rd.product_id = p.id
          WHERE r.type = 'OUTBOUND'
          ORDER BY r.created_at DESC
          """
    raw_data = query_db(sql)
    outbound_dict = {}

    for row in raw_data:
        rid = row['id']
        if rid not in outbound_dict:
            outbound_dict[rid] = {
                "id": rid,
                "warehouse": row['warehouse_name'],
                "staff": row['staff_name'],
                "customer": row['partner_name'],
                "created_at": str(row['created_at']),
                "items": []
            }
        outbound_dict[rid]['items'].append({
            "product": row['product_name'],
            "sku": row['sku'],
            "qty": row['quantity'],
            "price": row['price'],
            "total": row['quantity'] * row['price']
        })

    return jsonify(list(outbound_dict.values())), 200


@receipt_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_receipt(id):
    """
    API Xóa hoàn toàn thông tin một phiếu nhập hoặc xuất
    ---
    tags:
      - Receipt
    summary: Xóa phiếu nhập/xuất theo ID
    security:
      - Bearer: []
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
      401:
        description: "Chưa xác thực hoặc token không hợp lệ"
      403:
        description: "Bạn không có quyền thực hiện hành động này"
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
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
      abort(403, description="Bạn không có quyền thực hiện hành động này")
    exist_receipt = query_db("SELECT id FROM Receipts WHERE id = ?", (id,), one=True)
    if exist_receipt is None:
        return jsonify({"success": False, "message": "Thông tin phiếu không tồn tại"}), 404

    # FIX: dùng execute_db thay vì query_db để DELETE
    success = execute_db("DELETE FROM Receipts WHERE id = ?", (id,))
    if success:
        return jsonify({"success": True, "message": "Xóa thông tin phiếu thành công"}), 200
    else:
        return jsonify({"success": False, "message": "Đã có lỗi khi xóa thông tin phiếu"}), 500