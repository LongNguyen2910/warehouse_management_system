from flask import Blueprint, request, jsonify
from db_helper import query_db, execute_db
from datetime import datetime

logistics_bp = Blueprint('logistics', __name__)

VALID_STATUS = ["PICKING", "SHIPPING", "DELIVERED"]
@logistics_bp.route('/shipments', methods=['GET'])
def get_shipments():
    """
    Get all shipments
    ---
    tags:
      - Shipments
    responses:
      200:
        description: List of shipments
      500:
        description: Database error
    """
    try:
        shipments = query_db("SELECT * FROM Shipments")
        return jsonify(shipments)
    except:
        return jsonify({"error": "Database error"}), 500

@logistics_bp.route('/shipments', methods=['POST'])
def create_shipment():
    """
    Create shipment
    ---
    tags:
      - Shipments
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - transfer_id
            - driver_name
            - license_plate
            - expected_delivery_at
          properties:
            transfer_id:
              type: integer
              description: Mã vận chuyển
              example: 1
            driver_name:
              type: string
            license_plate:
              type: string
            expected_delivery_at:
              type: string
              format: date-time
              example: "2026-03-26T10:00:00"
    responses:
      200:
        description: Shipment created
      400:
        description: Missing or invalid input
      500:
        description: Failed to create shipment
    """

    data = request.json

    # validate input
    if not all(k in data for k in ("transfer_id", "driver_name", "license_plate", "expected_delivery_at")):
        return jsonify({"error": "Missing input"}), 400

    # validate datetime
    try:
        expected_time = datetime.fromisoformat(data['expected_delivery_at'])
    except:
        return jsonify({"error": "Invalid datetime format"}), 400

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
        return jsonify({"error": "Create shipment failed"}), 500

    return jsonify({"message": "Shipment created"})

@logistics_bp.route('/shipments/<int:id>', methods=['PUT'])
def update_shipment(id):
    """
    Update shipment status
    ---
    tags:
      - Shipments
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [PICKING, SHIPPING, DELIVERED]
    responses:
      200:
        description: Shipment updated successfully
      400:
        description: Invalid status
      404:
        description: Shipment not found
      500:
        description: Update failed
    """

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    status = data.get("status")

    # validate status
    if status not in VALID_STATUS:
        return jsonify({"error": "Invalid status"}), 400

    # check shipment tồn tại
    shipment = query_db(
        "SELECT * FROM Shipments WHERE id=?",
        (id,),
        one=True
    )

    if not shipment:
        return jsonify({"error": "Shipment not found"}), 404

    # update status
    success = execute_db(
        "UPDATE Shipments SET status=? WHERE id=?",
        (status, id)
    )

    if not success:
        return jsonify({"error": "Update failed"}), 500

    late = False
    if status == "DELIVERED":

        now = datetime.now()

        # 1. update actual_delivery_at
        success = execute_db(
            "UPDATE Shipments SET status=?, actual_delivery_at=? WHERE id=?",
            (status, now, id)
        )

        # 2. check late
        if shipment.get("expected_delivery_at"):
            if now > shipment["expected_delivery_at"]:
                late = True

        # 3. lấy transfer
        transfer = query_db(
            "SELECT * FROM Transfer_Orders WHERE id=?",
            (shipment['transfer_id'],),
            one=True
        )
        if not transfer:
            return jsonify({"error": "Transfer not found"}), 404

        # 4. lấy danh sách sản phẩm
        details = query_db(
            "SELECT * FROM Transfer_Details WHERE transfer_id=?",
            (shipment['transfer_id'],)
        )

        # 5. cộng kho đích
        for item in details:
            execute_db(
                """
                UPDATE Inventory
                SET quantity = quantity + ?
                WHERE warehouse_id=? AND product_id=?
                """,
                (item['quantity'], transfer['to_warehouse_id'], item['product_id'])
            )
            execute_db(
                """
                INSERT INTO Inventory_Logs
                    (product_id, warehouse_id, change_amount, action_type, reference_id)
                VALUES (?, ?, ?, 'TRANSFER_IN', ?)
                """,
                (item['product_id'], transfer['to_warehouse_id'], item['quantity'], transfer['id'])
            )
    else:
        success = execute_db(
            "UPDATE Shipments SET status=? WHERE id=?",
            (status, id)
        )

    return jsonify({
        "message": "Shipment updated successfully",
        "late": late
    })