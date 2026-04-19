from werkzeug.security import check_password_hash
from flask import Blueprint, jsonify, abort
import flask
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jwt_identity
from db_helper import query_db
from validate_helper import is_empty
from flask import make_response
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['POST'])
def login():
    """
    API Đăng nhập để lấy Access Token
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: 123456
            remember_me:
              type: boolean
              example: false
              description: "Nếu true, token sẽ hết hạn sau 30 ngày. Nếu false, token sẽ hết hạn sau 1 giờ"
    responses:
      200:
        description: "Đăng nhập thành công, Access Token được lưu vào HTTP-Only Cookie"
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Đăng nhập thành công"
            user_info:
              type: object
              properties:
                username:
                  type: string
                  example: "admin"
                role:
                  type: string
                  example: "ADMIN"
      400:
        description: "Tên đăng nhập và mật khẩu không được để trống"
      401:
        description: "Tên đăng nhập hoặc mật khẩu không đúng"
    """
    payload = flask.request.get_json(silent=True) or {}
    user_name = payload.get("username")
    password = payload.get("password")

    if is_empty(user_name) or is_empty(password):
        abort(400, description="Tên đăng nhập và mật khẩu không được để trống")

    # 1. Truy vấn SQL Server xem user có tồn tại không
    user = query_db("SELECT Users.id, username, role_name, password_hash FROM Users JOIN Roles ON Users.role_id = Roles.id WHERE username like ?", 
                    ('%' + user_name + '%',), one=True)
    
    if not user:
        abort(401, description="Tên đăng nhập hoặc mật khẩu không đúng")

    if user and check_password_hash(user['password_hash'], password):
      # 2. Nếu đúng, tạo Access Token
      # giấu 'role' vào trong identity hoặc claims để sau này kiểm tra quyền
      access_token = create_access_token(
        identity=str(user['id']), 
        additional_claims={"role": user['role_name'], "username": user['username']}
      )
      remember_me = payload.get("remember_me", False)
      expires_delta = 2592000 if remember_me else 86400

      response = make_response(jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "user_info": {
          "username": user['username'],
          "role": user['role_name']
        }
      }))
      
      # Set HTTP-Only Cookie
      response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=True,
        samesite='None',
        max_age=expires_delta
      )
      
      return response, 200

    abort(401, description="Tên đăng nhập hoặc mật khẩu không đúng")

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    API Đăng xuất
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: "Đăng xuất thành công, Cookie đã được xóa"
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Đăng xuất thành công"
      401:
        description: "Chưa xác thực hoặc token không hợp lệ"
    """
    response = make_response(jsonify({
      "success": True,
      "message": "Đăng xuất thành công"
    }))
    
    response.set_cookie(
      'access_token',
      '',
      httponly=True,
      secure=True,
      samesite='None',
      max_age=0 
    )
    
    return response, 200