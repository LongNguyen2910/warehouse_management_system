from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db
from datetime import datetime

logistics_bp = Blueprint('logistics', __name__)

VALID_STATUS = ["PICKING", "SHIPPING", "DELIVERED"]

@logistics_bp.route('/shipments', methods=['GET'])
def get_shipments():
    shipments = query_db("SELECT * FROM Shipments")

    return jsonify({
        "success": True,
        "data": shipments
    })

@logistics_bp.route('/shipments', methods=['POST'])
def create_shipment():
    data = request.json
    if not data:
        abort(400, "Invalid JSON")

    required = ["transfer_id", "driver_name", "license_plate", "expected_delivery_at"]
    if not all(k in data for k in required):
        abort(400, "Missing fields")

    # check transfer tồn tại
    transfer = query_db(
        "SELECT * FROM Transfer_Orders WHERE id=?",
        (data['transfer_id'],),
        one=True
    )

    if not transfer:
        abort(404, "Transfer not found")

    expected_time = datetime.fromisoformat(data['expected_delivery_at'])

    success = execute_db(
        """
        INSERT INTO Shipments 
        (transfer_id, driver_name, license_plate, status, expected_delivery_at)
        VALUES (?, ?, ?, 'PICKING', ?)
        """,
        (
            data['transfer_id'],
            data['driver_name'],
            data['license_plate'],
            expected_time
        )
    )

    if not success:
        abort(500, "Create failed")

    return jsonify({
        "success": True,
        "data": "Shipment created"
    })

@logistics_bp.route('/shipments/<int:id>', methods=['PUT'])
def update_shipment(id):
    data = request.json
    if not data:
        abort(400, "Invalid JSON")

    shipment = query_db(
        "SELECT * FROM Shipments WHERE id=?",
        (id,),
        one=True
    )

    if not shipment:
        abort(404, "Shipment not found")

    old_status = shipment['status']   # FIX: lưu trạng thái cũ

    status = data.get("status")
    driver_name = data.get("driver_name")
    license_plate = data.get("license_plate")

    if status and status not in VALID_STATUS:
        abort(400, "Invalid status")

    fields = []
    values = []

    if status:
        fields.append("status=?")
        values.append(status)

    if driver_name:
        fields.append("driver_name=?")
        values.append(driver_name)

    if license_plate:
        fields.append("license_plate=?")
        values.append(license_plate)

    if not fields:
        abort(400, "No data to update")

    # nếu giao xong → lưu thời gian thực tế
    if status == "DELIVERED":
        fields.append("actual_delivery_at=?")
        values.append(datetime.now())

    values.append(id)

    success = execute_db(
        f"UPDATE Shipments SET {', '.join(fields)} WHERE id=?",
        tuple(values)
    )

    if not success:
        abort(500, "Update failed")
    # UPDATE TRANSFER STATUS

    # khi đang vận chuyển
    if status == "SHIPPING":
        execute_db(
            "UPDATE Transfer_Orders SET status='SHIPPING' WHERE id=?",
            (shipment['transfer_id'],)
        )

    # FIX: tránh cộng kho nhiều lần
    if old_status != "DELIVERED" and status == "DELIVERED":

        transfer = query_db(
            "SELECT * FROM Transfer_Orders WHERE id=?",
            (shipment['transfer_id'],),
            one=True
        )

        details = query_db(
            "SELECT * FROM Transfer_Details WHERE transfer_id=?",
            (shipment['transfer_id'],)
        )

        # cộng kho đích
        for item in details:
            execute_db(
                """
                UPDATE Inventory
                SET quantity = quantity + ?
                WHERE warehouse_id=? AND product_id=?
                """,
                (item['quantity'], transfer['to_warehouse_id'], item['product_id'])
            )

        # update transfer → COMPLETED
        execute_db(
            "UPDATE Transfer_Orders SET status='COMPLETED' WHERE id=?",
            (shipment['transfer_id'],)
        )

    return jsonify({
        "success": True,
        "data": "Shipment updated"
    })

@logistics_bp.route('/shipments/<int:id>', methods=['DELETE'])
def delete_shipment(id):

    shipment = query_db(
        "SELECT * FROM Shipments WHERE id=?",
        (id,),
        one=True
    )

    if not shipment:
        abort(404, "Shipment not found")

    # 🔥 FIX: không cho xoá nếu đã giao
    if shipment['status'] == "DELIVERED":
        abort(400, "Cannot delete delivered shipment")

    success = execute_db(
        "DELETE FROM Shipments WHERE id=?",
        (id,)
    )

    if not success:
        abort(500, "Delete failed")

    return jsonify({
        "success": True,
        "data": "Shipment deleted"
    })