import os
import re

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
import pyodbc

from auth_api import auth_bp
from inventory_api import inventory_bp
from logistics_api import logistics_bp
from reports_api import reports_bp
from users_api import users_bp
from roles_api import roles_bp
from warehouses_api import warehouses_bp
from product_api import products_bp
app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

app.config['SWAGGER'] = {
    'title': 'WMS API - Nhóm 4',
    'uiversion': 3,
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Nhập Token theo định dạng: Bearer <your_token_here>"
        }
    }
}
swagger = Swagger(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(logistics_bp, url_prefix='/api/logistics')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(roles_bp, url_prefix='/api/roles')
app.register_blueprint(warehouses_bp, url_prefix='/api/warehouses')
app.register_blueprint(roles_bp, url_prefix='/api/roles')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(roles_bp, url_prefix='/api/roles')

@app.errorhandler(Exception)
def handle_exception(e):
    # Global error handler to catch all unhandled exceptions and return a consistent JSON response.
    # Use
    #   404: Not Found for resources that don't exist (e.g., invalid endpoint, missing product)
    #   400: Bad Request for invalid input data (e.g., missing required fields, invalid data types)
    #   401: Unauthorized for authentication issues (e.g., missing/invalid token)
    #   403: Forbidden for authorization issues (e.g., user role doesn't have permission to perform action)
    #   409: Conflict for database constraint violations (e.g., trying to delete a warehouse that has inventory items linked to it)
    #   500: Internal Server Error for unexpected issues in the server code (e.g., database errors, unhandled exceptions)
    # Using abort() to catch HTTP exceptions
    # Example:
    #     abort(404, description="Sản phẩm này không tồn tại trong kho")

    # HTTP Exceptions (404, 500, etc.)
    if isinstance(e, HTTPException):
        return jsonify({
            "success": False,
            "error_code": f"HTTP_{e.code}",
            "message": e.description,
        }), e.code
    if isinstance(e, pyodbc.Error):
        error_msg = str(e)
        if "547" in error_msg:
            match = re.search(r'constraint "FK_([^_]+)_([^"]+)"', error_msg)

            if match:
                table_con = match.group(1)
                table_cha = match.group(2)
                friendly_message = f"Không thể xóa bản ghi này vì đang có dữ liệu liên kết tại bảng '{table_con}'."
            else:
                friendly_message = "Không thể xóa do vi phạm ràng buộc dữ liệu liên quan."

        return jsonify({
            "success": False,
            "error_code": "DB_FOREIGN_KEY_CONFLICT",
            "message": friendly_message
        }), 409

        # Logic errors (in Python code) or unexpected exceptions
    response = {
        "success": False,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "System encountered an unexpected error. Please try again later."
    }

    # If in debug mode, include exception details for easier troubleshooting
    if app.config.get("DEBUG"):
        response["details"] = str(e)

    return jsonify(response), 500


# 1. Lỗi khi không gửi Token kèm theo
@jwt.unauthorized_loader
def my_unauthorized_callback(err_str):
    return jsonify({
        "success": False,
        "error_code": "MISSING_TOKEN",
        "message": "Vui lòng cung cấp Access Token trong Header"
    }), 401


# 2. Lỗi khi Token đã hết hạn
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "success": False,
        "error_code": "TOKEN_EXPIRED",
        "message": "Phiên đăng nhập đã hết hạn, vui lòng login lại"
    }), 401


# 3. Lỗi khi Token bị sai, bị sửa đổi
@jwt.invalid_token_loader
def my_invalid_token_callback(err_str):
    return jsonify({
        "success": False,
        "error_code": "INVALID_TOKEN",
        "message": "Token không hợp lệ hoặc đã bị chỉnh sửa"
    }), 401


if __name__ == '__main__':
    app.run(debug=True)