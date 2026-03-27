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
                WHERE i.quantity > 0 
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
                HAVING ISNULL(SUM(i.quantity), 0) <= p.min_stock 
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
            w.name AS warehouse_name,
            l.change_amount,
            l.action_type,
            l.reference_id,
            l.created_at
        FROM Inventory_Logs l
        JOIN Products p ON l.product_id = p.id
        LEFT JOIN Warehouses w ON l.warehouse_id = w.id
        WHERE p.sku = ?
        AND l.action_type <> 'TRANSFER'
        ORDER BY l.created_at DESC
        """
        results = query_db(query, (sku,))
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500
@reports_bp.route('/transfer-history', methods=['GET'])
def getTransferHistory():
    try:
        sku = flask.request.args.get('sku')
        query = """
        SELECT 
            p.sku,
            p.name AS product_name,
            w_from.name AS from_warehouse,
            w_to.name AS to_warehouse,
            td.quantity,
            ISNULL(u.username, 'System') AS staff,
            t.status,
            t.created_at
        FROM Transfer_Details td
        JOIN Transfer_Orders t ON td.transfer_id = t.id
        JOIN Products p ON td.product_id = p.id
        JOIN Warehouses w_from ON t.from_warehouse_id = w_from.id
        JOIN Warehouses w_to ON t.to_warehouse_id = w_to.id
        LEFT JOIN Users u ON t.staff_id = u.id
        """
        params = []
        if sku:
            query += " AND p.sku = ?"
            params.append(sku)
        query += " ORDER BY t.created_at DESC"
        results = query_db(query, tuple(params))
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500

@reports_bp.route('/receipt', methods=['GET'])
def getReceiptHistory():
    try:
        query = """ 
SELECT
    r.id AS receipt_id,
    r.type,
    w.name AS warehouse_name,
    p.sku,
    p.name AS product_name,
    rd.quantity,
    rd.price,
    (rd.quantity * rd.price) AS total_value,
    ISNULL(u.username, 'System') AS staff,
    r.partner_name,
    r.created_at
FROM Receipts r
JOIN Receipt_Details rd ON r.id = rd.receipt_id
JOIN Products p ON rd.product_id = p.id
JOIN Warehouses w ON r.warehouse_id = w.id
LEFT JOIN Users u ON r.staff_id = u.id
ORDER BY r.created_at DESC
        """
        results = query_db(query)
        return flask.jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500
@reports_bp.route('/export/excel', methods=['GET'])
def export():
    try:
        output = io.BytesIO()
        #Ton Kho
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
        #Low-stock
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
        #In and out
        query3 = """
                 SELECT TOP 100 p.sku, 
                                p.name AS product_name,
                                w.name AS warehouse_name,
                                l.change_amount,
                                l.action_type,
                                l.created_at
                    FROM Inventory_Logs l
                            JOIN Products p ON l.product_id = p.id
                            LEFT JOIN Warehouses w ON l.warehouse_id = w.id
                            WHERE l.action_type <> 'TRANSFER'
                            ORDER BY l.created_at DESC 
                 """
        data3 = query_db(query3)
        df3 = pd.DataFrame(data3)
        #Transfer
        query4 = """
                 SELECT p.sku, 
                        p.name AS product_name, 
                        w_from.name AS from_warehouse, 
                        w_to.name AS to_warehouse, 
                        td.quantity, 
                        ISNULL(u.username, 'System') AS staff, 
                        t.status, 
                        t.created_at
                 FROM Transfer_Details td
                          JOIN Transfer_Orders t ON td.transfer_id = t.id
                          JOIN Products p ON td.product_id = p.id
                          JOIN Warehouses w_from ON t.from_warehouse_id = w_from.id
                          JOIN Warehouses w_to ON t.to_warehouse_id = w_to.id
                          LEFT JOIN Users u ON t.staff_id = u.id
                 ORDER BY t.created_at DESC 
                 """
        data4 = query_db(query4)
        df4 = pd.DataFrame(data4)
        #Receipts
        query5 = """
                SELECT r.id AS receipt_id,
                        r.type,
                        w.name AS warehouse_name,
                        p.sku,
                        p.name AS product_name,
                        rd.quantity,
                        rd.price,
                        (rd.quantity * rd.price) AS total_value,
                        ISNULL(u.username, 'System') AS staff,
                        r.partner_name,
                        r.created_at
                FROM Receipts r
                            JOIN Receipt_Details rd ON r.id = rd.receipt_id
                            JOIN Products p ON rd.product_id = p.id
                            JOIN Warehouses w ON r.warehouse_id = w.id
                            LEFT JOIN Users u ON r.staff_id = u.id
                ORDER BY r.created_at DESC
                 """
        data5 = query_db(query5)
        df5 = pd.DataFrame(data5)
        #Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='TonKho', index=False)
            df2.to_excel(writer, sheet_name='LowStock', index=False)
            df3.to_excel(writer, sheet_name='History', index=False)
            df4.to_excel(writer, sheet_name='Transfer', index=False)
            df5.to_excel(writer, sheet_name='Receipts', index=False)

            for sheet_name, df in {
                'TonKho': df1,
                'LowStock': df2,
                'History': df3,
                'Transfer': df4,
                'Receipts': df5
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