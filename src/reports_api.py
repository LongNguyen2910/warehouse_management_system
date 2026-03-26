import flask
from flask import Blueprint
from db_helper import query_db
import pandas as pd
from flask import send_file
import io

reports_bp = Blueprint('reports', __name__)
@reports_bp.route('', methods=['GET'])
def getTonKho():
    try:
        query = """
                SELECT
                    i.id,
                    i.warehouse_id,
                    w.name AS warehouse_name,
                    i.product_id,
                    p.name AS product_name,
                    i.quantity
                FROM Inventory i
                         JOIN Products p ON i.product_id = p.id
                         JOIN Warehouses w ON i.warehouse_id = w.id
                WHERE i.quantity > 0 \
                """
        results = query_db(query)
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500
@reports_bp.route('/low-stock', methods=['GET'])
def getLowStock():
    try:
        query = """
                SELECT
                    p.id AS product_id,
                    p.name AS product_name,
                    p.min_stock,
                    ISNULL(SUM(i.quantity), 0) AS total_quantity,
                    (p.min_stock - ISNULL(SUM(i.quantity), 0)) AS need_to_import
                FROM Products p
                         LEFT JOIN Inventory i ON p.id = i.product_id
                GROUP BY p.id, p.name, p.min_stock
                HAVING ISNULL(SUM(i.quantity), 0) <= p.min_stock \
                """
        results = query_db(query)
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500
@reports_bp.route('/history/<string:sku>', methods=['GET'])
def getInventoryHistory(sku):
    try:
        query = """
                SELECT
                    l.id,
                    p.sku,
                    p.name AS product_name,
                    l.warehouse_id,
                    w.name AS warehouse_name,
                    l.change_amount,
                    l.action_type,
                    l.reference_id,
                    l.created_at
                FROM Inventory_Logs l
                         JOIN Products p ON l.product_id = p.id
                         LEFT JOIN Warehouses w ON l.warehouse_id = w.id
                WHERE p.sku = ?
                ORDER BY l.created_at DESC \
                """
        results = query_db(query, (sku,))
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500
@reports_bp.route('/export/excel', methods=['GET'])
def export_excel():
    try:
        query = """
        SELECT 
            i.id,
            w.name AS warehouse_name,
            p.sku,
            p.name AS product_name,
            i.quantity
        FROM Inventory i
        JOIN Products p ON i.product_id = p.id
        JOIN Warehouses w ON i.warehouse_id = w.id
        WHERE i.quantity > 0
        """
        data = query_db(query)
        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return send_file(
            output,
            download_name="inventory_report.xlsx",
            as_attachment=True
        )
    except Exception as e:
        return {"error": str(e)}, 500