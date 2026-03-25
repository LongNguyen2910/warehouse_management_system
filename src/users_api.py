from flask import Blueprint
users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['POST'])
def register():
   """
    API Đăng ký tài khoản người dùng mới
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
              description: Tên đăng nhập mong muốn
              example: "nhanvien01"
            password:
              type: string
              format: password
              description: Mật khẩu (nên có ít nhất 6 ký tự)
              example: "123456"
            role:
              type: string
              description: Vai trò trong hệ thống (Admin/Staff)
              enum: ["Admin", "Staff"]
              default: "Staff"
              example: "Staff"
    responses:
      200:
        description: Đăng ký thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
    """
   return "Đăng ký tài khoản mới"