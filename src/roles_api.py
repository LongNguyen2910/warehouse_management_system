from flask import Blueprint, abort, jsonify
import flask
from db_helper import query_db
roles_bp = Blueprint('roles', __name__)

@roles_bp.route('/', methods=['GET'])
def get_roles():
    """
    API Lấy danh sách các vai trò (Roles) có trong hệ thống
    ---
    tags:
      - Roles
    responses:
      200:
        description: Danh sách các quyền hiện có
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            roles:
              type: array
              items:
                type: string
              example: ["Admin", "Staff", "Manager", "Delivery person"]
    """
    roles = query_db("SELECT * FROM Roles")
    return jsonify(roles), 200

@roles_bp.route('/', methods=['POST'])
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
        description: Đăng ký thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    role_name = flask.request.json["role_name"]
    if not role_name:
        abort(400, description="Tên vai trò không được để trống")
    
    