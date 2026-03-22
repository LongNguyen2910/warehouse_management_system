from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from werkzeug.exceptions import HTTPException
from db_helper import get_db_connection

from auth_api import auth_bp
from inventory_api import inventory_bp
from logistics_api import logistics_bp
from reports_api import reports_bp

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

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({
            "success": False,
            "error_code": e.name.upper().replace(" ", "_"),
            "message": e.description
        }), e.code
    
    print(f"Error System: {str(e)}")
    response = {
        "success": False,
        "message": "Error, Check again",
        "error_details": str(e)
    }
    return jsonify(response), 500

if __name__ == '__main__':
    app.run()
