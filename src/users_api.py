from flask import Blueprint, abort, jsonify
import flask
from flask_jwt_extended import get_jwt, jwt_required
from werkzeug.security import generate_password_hash
from db_helper import execute_db, query_db
from validate_helper import is_empty, validate_password_strength
users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['POST'])
def register():
  """
  API Đăng ký tài khoản người dùng mới
  ---
  tags:
    - Users
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
          user_name:
            type: string
            description: Tên đăng nhập mong muốn
            example: "nhanvien01"
          password:
            type: string
            format: password
            description: Mật khẩu (nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số)
            example: "B$ecure2026"
  responses:
    200:
      description: Đăng ký thành công
    400:
      description: "Yêu cầu không hợp lệ (ví dụ: thiếu tên đăng nhập, mật khẩu yếu, hoặc tên đăng nhập đã tồn tại)"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    500:
      description: "Đã xảy ra lỗi khi tạo tài khoản"
  """
  payload = flask.request.get_json(silent=True) or {}
  user_name = payload.get("user_name")
  password = payload.get("password")

  if is_empty(user_name) or is_empty(password):
    abort(400, description="Tên đăng nhập và mật khẩu không được để trống")
  user_name = user_name.strip()
  if len(user_name) < 3 or len(user_name) > 50 or ' ' in user_name:
    abort(400, description="Tên đăng nhập phải có độ dài từ 3 đến 50 ký tự và không được chứa khoảng trắng")
  existing = query_db("SELECT id FROM Users WHERE username = ?", (user_name,), one=True)
  if existing:
    abort(400, description="Tên đăng nhập đã tồn tại")
  password = password.strip()
  if not validate_password_strength(password):
    abort(400, description="Mật khẩu yếu. Mật khẩu nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số.")
  password = generate_password_hash(password)

  role_id = query_db("SELECT id FROM Roles WHERE role_name = 'STAFF'", one=True)
  print(role_id)

  success = execute_db("INSERT INTO Users (username, password_hash, role_id) VALUES (?, ?, ?)", (user_name, password, role_id['id']))
  if success:
    return jsonify({"success": True, "message": "Tài khoản mới đã được tạo"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi tạo tài khoản")

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
  """
  API Lấy danh sách các người dùng có trong hệ thống
  ---
  tags:
    - Users
  security:
    - Bearer: []
  parameters:
    - name: id
      in: query
      required: false
      type: integer
    - name: username
      in: query
      required: false
      type: string
  responses:
    200:
      description: Danh sách người dùng
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
                  enum: ["MANAGER", "STAFF", "ADMIN", "DELIVERY MAN"]
                  example: "ADMIN"
                username:
                  type: string
                  example: "nhanvien01"
                created_at:
                  type: string
                  format: date-time
                  example: "Thu, 26 Mar 2026 15:53:41 GMT"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Không tim thấy người dùng nào phù hợp với tiêu chí tìm kiếm"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  id = flask.request.args.get("id")
  username = flask.request.args.get("username")
  query = "SELECT Users.id, Users.username, Roles.role_name, Users.created_at FROM Users JOIN Roles ON Users.role_id = Roles.id WHERE"
  data = ()
  if id:
    query += " Users.id = ? "
    data += (id,)
  if username:
    if id:
      query += " AND"
    query += " Users.username like ?"
    data += ('%' + username + '%',)
  if not id and not username:
    users = query_db("SELECT Users.id, Users.username, Roles.role_name, Users.created_at FROM Users JOIN Roles ON Users.role_id = Roles.id")
  else:
    users = query_db(query, data)
  if not users:
    return jsonify({"success": False, "message": "Không tìm thấy người dùng nào phù hợp với tiêu chí tìm kiếm"}), 404
  return jsonify({"success": True, "data": users}), 200

@users_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def change_password(id):
  """
  API Đổi mật khẩu người dùng
  ---
  tags:
    - Users
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
          password:
            type: string
            format: password
            description: Mật khẩu mới (nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số)
            example: "B$ecure2026"
  responses:
    200:
      description: Cập nhật thành công
    400:
      description: "Mật khẩu mới yếu"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    404:
      description: "Không tìm thấy người dùng với ID đã cho"
    500:
      description: "Đã xảy ra lỗi khi cập nhật mật khẩu"
  """
  payload = flask.request.get_json(silent=True) or {}
  password = payload.get("password")
  if is_empty(password):
    abort(400, description="Mật khẩu không được để trống")
  password = password.strip()
  if not validate_password_strength(password):
    abort(400, description="Mật khẩu yếu. Mật khẩu nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số.")
  password = generate_password_hash(password)

  existing = query_db("SELECT id FROM Users WHERE id = ?", (id,), one=True)
  if not existing:
    abort(404, description="Không tìm thấy người dùng với ID đã cho")

  success = execute_db("UPDATE Users SET password_hash = ? WHERE id = ?", (password, id))
  if success:
    return jsonify({"success": True, "message": "Mật khẩu đã được cập nhật"}), 200
  else:
      abort(500, description="Đã xảy ra lỗi khi cập nhật mật khẩu")

@users_bp.route('/', methods=['PUT'])
@jwt_required()
def update_user_role():
  """
  API Cập nhật vai trò của người dùng
  ---
  tags:
    - Users
  security:
    - Bearer: []
  parameters:
    - name: body
      in: body
      required: true
      schema:
        type: object
        properties:
          user_id:
            type: integer
            description: ID của người dùng cần cập nhật vai trò
            example: 1
          role_id:
            type: integer
            description: ID của vai trò mới
            example: 2
  responses:
    200:
      description: Vai trò của người dùng đã được cập nhật
    400:
      description: "Yêu cầu không hợp lệ"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Không tìm thấy người dùng hoặc vai trò với ID đã cho"
    500:
      description: "Đã xảy ra lỗi khi cập nhật vai trò của người dùng"
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  payload = flask.request.get_json(silent=True) or {}
  user_id = payload.get("user_id")
  role_id = payload.get("role_id")
  if not user_id or not role_id:
    abort(400, description="ID của người dùng và vai trò không được để trống")
  existing_user = query_db("SELECT id FROM Users WHERE id = ?", (user_id,), one=True)
  if not existing_user:
    abort(404, description="Không tìm thấy người dùng với ID đã cho")
  existing_role = query_db("SELECT id FROM Roles WHERE id = ?", (role_id,), one=True)
  if not existing_role:
    abort(404, description="Không tìm thấy vai trò với ID đã cho")
  success = execute_db("UPDATE Users SET role_id = ? WHERE id = ?", (role_id, user_id))
  if success:
    return jsonify({"success": True, "message": "Vai trò của người dùng đã được cập nhật"}), 200
  else:
    abort(500, description="Đã xảy ra lỗi khi cập nhật vai trò của người dùng")


@users_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
  """
  API Xóa người dùng
  ---
  tags:
    - Users
  security:
    - Bearer: []
  parameters:
    - name: id
      in: path
      required: true
      type: integer
  responses:
    200:
      description: Người dùng đã được xóa
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
    403:
      description: "Bạn không có quyền thực hiện hành động này"
    404:
      description: "Không tìm thấy người dùng với ID đã cho"
    500:
      description: "Đã xảy ra lỗi khi xóa người dùng"
      description: "Không tìm thấy người dùng với ID đã cho"  
  """
  claims = get_jwt()
  if claims.get("role") != "ADMIN":
    abort(403, description="Bạn không có quyền thực hiện hành động này")
  existing = query_db("SELECT id FROM Users WHERE id = ?", (id,), one=True)
  if not existing:
    abort(404, description="Không tìm thấy người dùng với ID đã cho")

  execute_db("DELETE FROM Users WHERE id = ?", (id,))
  return jsonify({"success": True, "message": "Người dùng đã được xóa"}), 200

