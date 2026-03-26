import flask
from flask import Blueprint
from db_helper import query_db
import pandas as pd
from flask import send_file
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
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
@reports_bp.route('/export/pdf', methods=['GET'])
def export_pdf():
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
        query = """
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
        data = query_db(query)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20,
            rightMargin=20,
            topMargin=30,
            bottomMargin=20
        )
        styles = getSampleStyleSheet()
        table_data = [[
            Paragraph("<b>Warehouse</b>", styles["Normal"]),
            Paragraph("<b>SKU</b>", styles["Normal"]),
            Paragraph("<b>Product</b>", styles["Normal"]),
            Paragraph("<b>Quantity</b>", styles["Normal"])
        ]]
        for row in data:
            table_data.append([
                Paragraph(row["warehouse"], styles["Normal"]),
                Paragraph(row["sku"], styles["Normal"]),
                Paragraph(row["product"], styles["Normal"]),
                Paragraph(str(row["quantity"]), styles["Normal"])
            ])

        col_widths = [
            doc.width * 0.25,  # Warehouse
            doc.width * 0.15,  # SKU
            doc.width * 0.40,  # Product
            doc.width * 0.20   # Quantity
        ]

        table = Table(table_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Arial'),
            ('FONTSIZE', (0,0), (-1,-1), 10),

            # Header
            ('BACKGROUND', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),

            # Grid
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),

            # Align
            ('ALIGN', (3,1), (3,-1), 'CENTER'),

            # Padding
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))

        doc.build([table])
        buffer.seek(0)
        return send_file(
            buffer,
            download_name="inventory_report.pdf",
            as_attachment=True
        )
    except Exception as e:
        return {"error": str(e)}, 500