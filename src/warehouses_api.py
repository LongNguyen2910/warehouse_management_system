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
    - name: id
      in: query
      required: false
      type: integer
    - name: name
      in: query
      required: false
      type: string
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
                address:
                  type: string
                  example: "Nguyễn Trãi, Thanh Xuân, Hà Nội"
                capacity:
                  type: integer
                  example: 1000
                longitude:
                  type: number
                  format: float
                  example: 105.804817
                latitude:
                  type: number
                  format: float
                  example: 21.028511
    404:
      description: "Không tim thấy kho hàng nào phù hợp với tiêu chí tìm kiếm"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
  """
  id = flask.request.args.get("id")
  name = flask.request.args.get("name")
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
            latitude:
                type: number
                format: float
                description: Vĩ độ của kho hàng
                example: 21.028511
            longitude:
                type: number  
                format: float
                description: Kinh độ của kho hàng
                example: 105.804817
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
  longitude = payload.get("longitude")
  latitude = payload.get("latitude")
  if is_empty(warehouse_name):
    abort(400, description="Tên của kho hàng không được để trống")
  warehouse_name = warehouse_name.strip().upper()
  success = execute_db("INSERT INTO Warehouses (name, address, capacity, longitude, latitude) VALUES (?, ?, ?, ?, ?)", (warehouse_name, address, capacity, longitude, latitude))
  if success:
    return jsonify({"success": True, "message": "Kho hàng mới đã được tạo"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi tạo kho hàng mới")

@warehouses_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_warehouse(id):
  """
  API Cập nhật thông tin kho hàng
  ---
  tags:
    - Warehouses
  security:
    - Bearer: []
  parameters:
    - name: id
      in: path
      required: true
      type: integer
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
            latitude:
                type: number
                format: float
                description: Vĩ độ của kho hàng
                example: 21.028511
            longitude:
                type: number  
                format: float
                description: Kinh độ của kho hàng
                example: 105.804817
  responses:
    200:
      description: "Kho hàng đã được cập nhật"
    400:
      description: "Yêu cầu không hợp lệ (ví dụ: tên kho hàng bị trùng với kho hàng khác)"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Không tìm thấy kho hàng với ID đã cho"
    500:
      description: "Đã xảy ra lỗi khi cập nhật thông tin kho hàng"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  payload = flask.request.get_json(silent=True) or {}
  warehouse_name = payload.get("name")
  address = payload.get("address")
  capacity = payload.get("capacity")
  longitude = payload.get("longitude")
  latitude = payload.get("latitude")
  existing = query_db("SELECT id FROM Warehouses WHERE id = ?", (id,), one=True)
  if not existing:
    abort(404, description="Không tìm thấy kho hàng với ID đã cho")
  set_clauses = []
  data = []
  if warehouse_name is not None and warehouse_name.strip() != "":
    warehouse_name = warehouse_name.strip()
    set_clauses.append("name = ?")
    data.append(warehouse_name)
  if address is not None and address.strip() != "":
    address = address.strip()
    set_clauses.append("address = ?")
    data.append(address)
  if capacity is not None and capacity != "":
    capacity = int(capacity)
    set_clauses.append("capacity = ?")
    data.append(capacity)
  if longitude is not None and longitude != "":
    set_clauses.append("longitude = ?")
    data.append(longitude)
  if latitude is not None and latitude != "":
    set_clauses.append("latitude = ?")
    data.append(latitude)
  if not set_clauses:
    abort(400, description="Không có dữ liệu nào để cập nhật")
  execute_db(f"UPDATE Warehouses SET {', '.join(set_clauses)} WHERE id = ?", (*data, id))
  return jsonify({"success": True, "message": "Kho hàng đã được cập nhật"}), 200

@warehouses_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_warehouse(id):
  """
  API Xóa kho hàng
  ---
  tags:
    - Warehouses
  security:
    - Bearer: []
  parameters:
    - name: id
      in: path
      required: true
      type: integer
  responses:
    200:
      description: "Kho đã được xóa"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Không tìm thấy kho hàng với ID đã cho"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  existing = query_db("SELECT id FROM Warehouses WHERE id = ?", (id,), one=True)
  if not existing:
    abort(404, description="Không tìm thấy kho hàng với ID đã cho")
  execute_db("DELETE FROM Warehouses WHERE id = ?", (id,))
  return jsonify({"success": True, "message": "Kho đã được xóa"}), 200