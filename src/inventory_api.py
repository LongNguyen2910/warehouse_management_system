from pydoc import describe

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
                (int(quantity), exist_inventory[0])
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



