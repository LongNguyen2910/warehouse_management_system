from flask import Blueprint, abort, jsonify
import flask
from flask_jwt_extended import get_jwt, jwt_required
from db_helper import query_db, execute_db
from validate_helper import is_empty
roles_bp = Blueprint('roles', __name__)

@roles_bp.route('/', methods=['GET'])
@jwt_required()
def get_roles():
  """
  API Lấy danh sách các vai trò có trong hệ thống
  ---
  tags:
    - Roles
  parameters:
    - name: id
      in: query
      required: false
      type: integer
    - name: role_name
      in: query
      required: false
      type: string
  responses:
    200:
      description: Danh sách các quyền
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
                role_name:
                  type: string
                  example: "ADMIN"
    404:
      description: "Không tim thấy vai trò nào phù hợp với tiêu chí tìm kiếm"
  """
  id = flask.request.args.get("id")
  role_name = flask.request.args.get("role_name")
  query = "SELECT * FROM Roles WHERE"
  data = ()
  if id:
    query += " id = ? "
    data += (id,)
  if role_name:
    if id:
      query += " AND"
    query += " role_name = ?"
    data += (role_name,)
  if not id and not role_name:
    roles = query_db("SELECT * FROM Roles")
  else:
    roles = query_db(query, data)
  if not roles:
    return jsonify({"success": True, "message": "Không tìm thấy vai trò nào phù hợp với tiêu chí tìm kiếm"}), 404
  return jsonify({"success": True, "data": roles}), 200
  """
  API Lấy danh sách các vai trò có trong hệ thống
  ---
  tags:
    - Roles
  security:
    - Bearer: []
  parameters:
    - name: id
      in: query
      required: false
      type: integer
    - name: role_name
      in: query
      required: false
      type: string
  responses:
    200:
      description: Danh sách các quyền
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
                role_name:
                  type: string
                  example: "ADMIN"
    404:
      description: "Không tim thấy vai trò nào phù hợp với tiêu chí tìm kiếm"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
  """
  id = flask.request.args.get("id")
  role_name = flask.request.args.get("role_name")
  query = "SELECT * FROM Roles WHERE"
  data = ()
  if id:
    query += " id = ? "
    data += (id,)
  if role_name:
    if id:
      query += " AND"
    query += " role_name = ?"
    data += (role_name,)
  if not id and not role_name:
    roles = query_db("SELECT * FROM Roles")
  else:
    roles = query_db(query, data)
  if not roles:
    return jsonify({"success": True, "message": "Không tìm thấy vai trò nào phù hợp với tiêu chí tìm kiếm"}), 404
  return jsonify({"success": True, "data": roles}), 200

@roles_bp.route('/', methods=['POST'])
@jwt_required()
def create_role():
  """
  API Tạo vai trò mới
  ---
  tags:
    - Roles
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
          role_name:
            type: string
            description: Tên vai trò
            example: "Manager"
  responses:
    200:
      description: "Vai trò mới đã được tạo"
    400:
      description: "Yêu cầu không hợp lệ (ví dụ: thiếu tên vai trò hoặc vai trò đã tồn tại)"
    500:
      description: "Đã xảy ra lỗi khi tạo vai trò mới"
  """
  payload = flask.request.get_json(silent=True) or {}
  role_name = payload.get("role_name")
  if is_empty(role_name):
    abort(400, description="Tên vai trò không được để trống")
  role_name = role_name.strip().upper()
  existing = query_db("SELECT id FROM Roles WHERE role_name = ?", (role_name,), one=True)
  if existing:
    abort(400, description="Vai trò này đã tồn tại")
  success = execute_db("INSERT INTO Roles (role_name) VALUES (?)", (role_name,))
  if success:
    return jsonify({"success": True, "message": "Vai trò mới đã được tạo"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi tạo vai trò mới")
  """
  API Tạo vai trò mới
  ---
  tags:
    - Roles
  security:
    - Bearer: []
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
          role_name:
            type: string
            description: Tên vai trò
            example: "Manager"
  responses:
    200:
      description: "Vai trò mới đã được tạo"
    400:
      description: "Yêu cầu không hợp lệ (ví dụ: thiếu tên vai trò hoặc vai trò đã tồn tại)"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    500:
      description: "Đã xảy ra lỗi khi tạo vai trò mới"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  payload = flask.request.get_json(silent=True) or {}
  role_name = payload.get("role_name")
  if is_empty(role_name):
    abort(400, description="Tên vai trò không được để trống")
  role_name = role_name.strip().upper()
  existing = query_db("SELECT id FROM Roles WHERE role_name = ?", (role_name,), one=True)
  if existing:
    abort(400, description="Vai trò này đã tồn tại")
  success = execute_db("INSERT INTO Roles (role_name) VALUES (?)", (role_name,))
  if success:
    return jsonify({"success": True, "message": "Vai trò mới đã được tạo"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi tạo vai trò mới")

@roles_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_role(id):
  """
  API Cập nhật thông tin vai trò
  ---
  tags:
    - Roles
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
          role_name:
            type: string
            description: Tên vai trò
            example: "Manager"
  responses:
    200:
      description: "Vai trò đã được cập nhật"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Vai trò không tồn tại"
    500:
      description: "Đã xảy ra lỗi khi cập nhật vai trò"
    """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  payload = flask.request.get_json(silent=True) or {}
  role_name = payload.get("role_name")
  if role_name is None:
      abort(400, description="Tên vai trò không được để trống")
  role_name = role_name.strip().upper()
  success = execute_db("UPDATE Roles SET role_name = ? WHERE id = ?", (role_name, id))
  if success:
      return jsonify({"success": True, "message": "Vai trò đã được cập nhật"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi cập nhật vai trò")

@roles_bp.route('/<id>', methods=['DELETE'])
def delete_role(id):
  """
  API Xóa một vai trò
  ---
  tags:
    - Roles
  security:
    - Bearer: []
  parameters:
    - name: id
      in: path
      required: true
      type: integer
  responses:
    200:
      description: "Vai trò đã được xóa"
    405:
      description: "Không thể xóa vai trò này vì vẫn còn người dùng đang sử dụng vai trò này"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Vai trò không tồn tại"
    500:
      description: "Đã xảy ra lỗi khi xóa vai trò"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  dependency = query_db("SELECT id FROM Users WHERE role_id = ?", (id,), one=True)
  existing = query_db("SELECT id FROM Roles WHERE id = ?", (id,), one=True)
  if not existing:
      abort(404, description="Vai trò không tồn tại")
  success = execute_db("DELETE FROM Roles WHERE id = ?", (id,))
  return jsonify({"success": True, "message": "Vai trò đã được xóa"}), 200