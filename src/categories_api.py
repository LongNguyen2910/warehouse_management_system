from flask import Blueprint, abort, abort, jsonify
import flask
from flask_jwt_extended import get_jwt, get_jwt, jwt_required

from db_helper import execute_db, query_db
from validate_helper import is_empty

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
@jwt_required()
def get_categories():
  """
  API Lấy danh sách các danh mục có trong hệ thống
  ---
  tags:
    - Categories
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
      description: Danh sách các danh mục
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
                  example: "Điện tử"
    404:
      description: "Không tim thấy danh mục nào phù hợp với tiêu chí tìm kiếm"
    401:
      description: "Chưa xác thực hoặc token không hợp lệ"
  """
  id = flask.request.args.get("id")
  name = flask.request.args.get("name")
  query = "SELECT * FROM Categories WHERE"
  data = ()
  if id:
    query += " id = ? "
    data += (id,)
  if name:
    if id:
      query += " AND"
    query += " name = ?"
    data += (name,)
  if not id and not name:
    categories = query_db("SELECT * FROM Categories")
  else:
    categories = query_db(query, data)
  if not categories:
    return jsonify({"success": True, "message": "Không tìm thấy danh mục nào phù hợp với tiêu chí tìm kiếm"}), 404
  return jsonify({"success": True, "data": categories}), 200

@categories_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    """
    API Tạo mới một danh mục
    ---
    tags:
        - Categories
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
                    description: Tên danh mục
                    example: "Điện tử"
    responses:
        200:
            description: "Danh mục đã được tạo thành công"
            schema:
                type: object
                properties:
                    success:
                        type: boolean
                        example: true
                    message:
                        type: string
                        example: "Danh mục đã được tạo thành công"
        400:
            description: "Tên danh mục không được để trống"
        401:
            description: "Chưa xác thực hoặc token không hợp lệ"
        403:
            description: "Bạn không có quyền thực hiện hành động này"
        500:
            description: "Đã xảy ra lỗi khi tạo danh mục mới"
    """
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    category_name = payload.get("name")
    if is_empty(category_name):
        abort(400, description="Tên của danh mục không được để trống")
    category_name = category_name.strip().upper()
    existing = query_db("SELECT id FROM Categories WHERE name = ?", (category_name,), one=True)
    if existing:
        abort(400, description="Danh mục này đã tồn tại")
    success = execute_db("INSERT INTO Categories (name) VALUES (?)", (category_name,))
    if success:
        return jsonify({"success": True, "message": "Danh mục đã được tạo thành công"}), 200
    else:
        abort(500, description="Đã xảy ra lỗi khi tạo danh mục mới")

@categories_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_category(id):
    """
    API Cập nhật thông tin danh mục
    ---
    tags:
        - Categories
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
                description: Tên danh mục
                example: "Điện tử"
    responses:  
        200:
            description: "Danh mục đã được cập nhật"
        400:
            description: "Tên danh mục không được để trống"
        401:
            description: "Chưa xác thực hoặc token không hợp lệ"
        403:
            description: "Bạn không có quyền thực hiện hành động này"
        404:
            description: "Danh mục không tồn tại"
        500:
            description: "Đã xảy ra lỗi khi cập nhật danh mục"
    """
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    category_name = payload.get("name")
    if is_empty(category_name):
        abort(400, description="Tên của danh mục không được để trống")
    category_name = category_name.strip().upper()
    existing = query_db("SELECT id FROM Categories WHERE name = ?", (category_name,), one=True)
    if existing:
        abort(400, description="Danh mục này đã tồn tại")
    existing = query_db("SELECT id FROM Categories WHERE id = ?", (id,), one=True)
    if not existing:
        abort(404, description="Không tìm thấy danh mục với ID đã cho")
    success = execute_db("UPDATE Categories SET name = ? WHERE id = ?", (category_name, id))
    if success:
        return jsonify({"success": True, "message": "Danh mục đã được cập nhật"}), 200
    else:
        abort(500, description="Đã xảy ra lỗi khi cập nhật danh mục")

@categories_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    """
    API Xóa một danh mục
    ---
    tags:
        - Categories    
    security:
        - Bearer: []
    parameters:
        - name: id
          in: path
          required: true
          type: integer
    responses:
        200:
            description: "Danh mục đã được xóa"
        401:
            description: "Chưa xác thực hoặc token không hợp lệ"
        403:
            description: "Bạn không có quyền thực hiện hành động này"
        404:
            description: "Danh mục không tồn tại"
    """
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    existing = query_db("SELECT id FROM Categories WHERE id = ?", (id,), one=True)
    if not existing:
        abort(404, description="Không tìm thấy danh mục với ID đã cho")
    execute_db("DELETE FROM Categories WHERE id = ?", (id,))
    return jsonify({"success": True, "message": "Danh mục đã được xóa"}), 200