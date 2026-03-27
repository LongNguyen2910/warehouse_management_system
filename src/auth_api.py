from werkzeug.security import check_password_hash
from flask import Blueprint, jsonify, abort
import flask
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db_helper import query_db
from validate_helper import is_empty
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
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: 123456
    responses:
      200:
        description: "Đăng nhập thành công, trả về Access Token"
        schema:
            type: object
            properties:
                success:
                    type: boolean
                    example: true
                message:
                    type: string
                    example: "Đăng nhập thành công"
                access_token:
                    type: string
                    example: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
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
    # Chúng ta giấu 'role' vào trong identity hoặc claims để sau này kiểm tra quyền
        access_token = create_access_token(
            identity=str(user['id']), 
            additional_claims={"role": user['role_name'], "username": user['username']}
        )
        
        return jsonify({
            "success": True,
            "message": "Đăng nhập thành công",
            "access_token": access_token,
            "user_info": {
                "username": user['username'],
                "role": user['role_name']
            }
        }), 200
