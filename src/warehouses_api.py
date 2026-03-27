from flask import Blueprint, abort, abort, jsonify
import flask
from flask_jwt_extended import get_jwt, get_jwt, jwt_required

from db_helper import execute_db, query_db
from validate_helper import is_empty

warehouses_bp = Blueprint('warehouses', __name__)

@warehouses_bp.route('/', methods=['GET'])
@jwt_required()
def get_warehouses():
  """
  API Lấy danh sách các kho hàng có trong hệ thống
  ---
  tags:
    - Warehouses
  security:
    - Bearer: []
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
          id:
            type: string
            description: ID của kho hàng
            example: "WH001"
          name:
            type: string
            description: Tên kho hàng
            example: "Kho A"
  responses:
    200:
      description: Danh sách các kho hàng
      schema:
        type: object
        properties:
          success:
            type: boolean
          data:
            type: array
            items:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: "Kho A"
    404:
      description: "Không tim thấy kho hàng nào phù hợp với tiêu chí tìm kiếm"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
  """
  payload = flask.request.get_json(silent=True) or {}
  id = payload.get("id")
  name = payload.get("name")
  query = "SELECT * FROM Warehouses WHERE"
  data = ()
  if id:
    query += " id = ? "
    data += (id,)
  if name:
    if id:
      query += " AND"
    query += " name like ?"
    data += ('%' + name + '%',)
  if not id and not name:
    warehouses = query_db("SELECT * FROM Warehouses")
  else:
    warehouses = query_db(query, data)
  if not warehouses:
    return jsonify({"success": True, "message": "Không tìm thấy kho hàng nào phù hợp với tiêu chí tìm kiếm"}), 404
  return jsonify({"success": True, "data": warehouses}), 200

@warehouses_bp.route('/', methods=['POST'])
@jwt_required()
def create_warehouse():
  """
  API Tạo kho hàng mới
  ---
  tags:
    - Warehouses
  security:
    - Bearer: []
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
            name:
                type: string
                description: Tên kho hàng
                example: "Kho A"
            address:
                type: string
                description: Địa chỉ kho hàng
                example: "Nguyễn Trãi, Thanh Xuân, Hà Nội"
            capacity:
                type: integer
                description: Sức chứa tối đa của kho hàng
                example: 1000
  responses:
    200:
      description: "Kho hàng mới đã được tạo"
    400:
      description: "Yêu cầu không hợp lệ (ví dụ: thiếu tên kho hàng hoặc kho hàng đã tồn tại)"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"      
    500:
      description: "Đã xảy ra lỗi khi tạo kho hàng mới"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  payload = flask.request.get_json(silent=True) or {}
  warehouse_name = payload.get("name")
  address = payload.get("address")
  capacity = payload.get("capacity")
  if is_empty(warehouse_name) and is_empty(address) and is_empty(capacity):
    abort(400, description="Tên, địa chỉ và sức chứa của kho hàng không được để trống")
  warehouse_name = warehouse_name.strip().upper()
  success = execute_db("INSERT INTO Warehouses (name, address, capacity) VALUES (?, ?, ?)", (warehouse_name, address, capacity))
  if success:
    return jsonify({"success": True, "message": "Kho hàng mới đã được tạo"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi tạo kho hàng mới")

