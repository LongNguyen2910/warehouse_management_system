import flask
from flask import Blueprint
from db_helper import query_db
import pandas as pd
from flask import send_file
from openpyxl.utils import get_column_letter
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
def export():
    try:
        output = io.BytesIO()
        # ===== QUERY 1: TỒN KHO =====
        query1 = """
                 SELECT
                     w.name AS warehouse,
                     p.sku,
                     p.name AS product,
                     i.quantity
                 FROM Inventory i
                          JOIN Products p ON i.product_id = p.id
                          JOIN Warehouses w ON i.warehouse_id = w.id
                 WHERE i.quantity > 0 
                 """
        data1 = query_db(query1)
        df1 = pd.DataFrame(data1)
        # ===== QUERY 2: LOW STOCK =====
        query2 = """
                 SELECT
                     p.id AS product_id,
                     p.name AS product_name,
                     p.min_stock,
                     ISNULL(SUM(i.quantity), 0) AS total_quantity,
                     (p.min_stock - ISNULL(SUM(i.quantity), 0)) AS need_to_import
                 FROM Products p
                          LEFT JOIN Inventory i ON p.id = i.product_id
                 GROUP BY p.id, p.name, p.min_stock
                 HAVING ISNULL(SUM(i.quantity), 0) <= p.min_stock 
                 """
        data2 = query_db(query2)
        df2 = pd.DataFrame(data2)
        # ===== QUERY 3: HISTORY (OPTIONAL) =====
        query3 = """
                 SELECT TOP 100
            p.sku,
                     p.name AS product_name,
                        l.change_amount,
                        l.action_type,
                        l.created_at
                 FROM Inventory_Logs l
                          JOIN Products p ON l.product_id = p.id
                 ORDER BY l.created_at DESC 
                 """
        data3 = query_db(query3)
        df3 = pd.DataFrame(data3)

        #Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='TonKho', index=False)
            df2.to_excel(writer, sheet_name='LowStock', index=False)
            df3.to_excel(writer, sheet_name='History', index=False)

            for sheet_name, df in {
                'TonKho': df1,
                'LowStock': df2,
                'History': df3
            }.items():
                worksheet = writer.sheets[sheet_name]
                for col_idx, col in enumerate(df.columns, 1):
                    max_length = len(str(col))

                    for cell in df[col]:
                        if cell:
                            max_length = max(max_length, len(str(cell)))
                    adjusted_width = max_length + 2
                    col_letter = get_column_letter(col_idx)
                    worksheet.column_dimensions[col_letter].width = adjusted_width
        output.seek(0)
        return send_file(
            output,
            download_name="inventory_report.xlsx",
            as_attachment=True
        )
    except Exception as e:
        return {"error": str(e)}, 500