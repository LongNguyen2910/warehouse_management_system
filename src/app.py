from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from werkzeug.exceptions import HTTPException

from auth_api import auth_bp
from inventory_api import inventory_bp
from logistics_api import logistics_bp
from reports_api import reports_bp
from users_api import users_bp
from roles_api import roles_bp

app = Flask(__name__)

CORS(app) 

app.config['SWAGGER'] = {
    'title': 'WMS API - Nhóm 4',
    'uiversion': 3,
}
swagger = Swagger(app)


app.register_blueprint(auth_bp, url_prefix='/api/auth')   
app.register_blueprint(inventory_bp, url_prefix='/api/inventory') 
app.register_blueprint(logistics_bp, url_prefix='/api/logistics')
app.register_blueprint(reports_bp, url_prefix='/api/reports')    
app.register_blueprint(users_bp, url_prefix='/api/users')   
app.register_blueprint(roles_bp, url_prefix='/api/roles')  

@app.errorhandler(Exception)
def handle_exception(e):
    # Global error handler to catch all unhandled exceptions and return a consistent JSON response.
    # Use
    #   404: Not Found for resources that don't exist (e.g., invalid endpoint, missing product)
    #   400: Bad Request for invalid input data (e.g., missing required fields, invalid data types)
    #   500: Internal Server Error for unexpected issues in the server code (e.g., database errors, unhandled exceptions)
    # Using abort() to catch HTTP exceptions
    # Example:
    #     abort(404, description="Sản phẩm này không tồn tại trong kho")

    #HTTP Exceptions (404, 500, etc.)
    if isinstance(e, HTTPException):
        return jsonify({
            "success": False,
            "error_code": f"HTTP_{e.code}",
            "message": e.description,
        }), e.code
    
    #Logic errors (in Python code) or unexpected exceptions
    response = {
        "success": False,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "System encountered an unexpected error. Please try again later."
    }

    #If in debug mode, include exception details for easier troubleshooting
    if app.config.get("DEBUG"):
        response["details"] = str(e)
        
    return jsonify(response), 500


if __name__ == '__main__':
    app.run(debug=True)
