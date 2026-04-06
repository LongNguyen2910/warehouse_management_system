from flask import Blueprint, request, jsonify, abort
from db_helper import query_db, execute_db, get_db_connection
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
    shipments = query_db("SELECT * FROM Shipments")

    return jsonify({
        "success": True,
        "data": shipments
    })

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
              example: 1
            driver_name:
              type: string
              example: "Nguyen Van A"
            license_plate:
              type: string
              example: "51A-12345"
            expected_delivery_at:
              type: string
              format: date-time
              example: "2026-03-26T10:00:00"
    responses:
      200:
        description: Shipment created
      400:
        description: Invalid input
      404:
        description: Transfer not found
      500:
        description: Create failed
    """
    data = request.json
    if not data:
        abort(400, "Invalid JSON")

    required = ["transfer_id", "driver_name", "license_plate", "expected_delivery_at"]
    if not all(k in data for k in required):
        abort(400, "Missing fields")


    # check transfer tồn tại
    transfer = query_db(
        "SELECT * FROM Transfer_Orders WHERE id=? AND status='APPROVED'",
        (data['transfer_id'],),
        one=True
    )

    if not transfer:
        abort(404, "Transfer not found")
    # if user send format false
    try:
        expected_time = datetime.fromisoformat(data['expected_delivery_at'])
    except:
        abort(400, "Invalid datetime format")
    # check shipment đã tồn tại cho transfer_id chưa
    existing_shipment = query_db(
        "SELECT * FROM Shipments WHERE transfer_id=?",
        (data['transfer_id'],),
        one=True
    )

    if existing_shipment:
        abort(400, "Shipment for this Transfer ID already exists")
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


    return jsonify({
        "success": True,
        "data": "Shipment created"
    })
# edit
@logistics_bp.route('/shipments/<int:id>', methods=['PUT'])
def update_shipment(id):
    """
    Update shipment
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
          properties:
            status:
              type: string
              enum: ["PICKING", "SHIPPING", "DELIVERED"]
              example: "DELIVERED"
            driver_name:
              type: string
              example: "Tran Van B"
            license_plate:
              type: string
              example: "51B-67890"
    responses:
      200:
        description: Updated
      400:
        description: Invalid input
      404:
        description: Not found
      500:
        description: Update failed
    """
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
        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            for item in details:
                cursor.execute(
                    "SELECT * FROM Inventory WHERE warehouse_id=? AND product_id=?",
                    (transfer['to_warehouse_id'], item['product_id'])
                )
                inventory = cursor.fetchone()

                if not inventory:
                    abort(404, "Inventory not found")

                cursor.execute(
                    """
                    UPDATE Inventory
                    SET quantity = quantity + ?
                    WHERE warehouse_id = ?
                      AND product_id = ?
                    """,
                    (item['quantity'], transfer['to_warehouse_id'], item['product_id'])
                )

            cursor.execute(
                "UPDATE Transfer_Orders SET status='COMPLETED' WHERE id=?",
                (shipment['transfer_id'],)
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e


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
    """
    Delete shipment
    ---
    tags:
      - Shipments
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Deleted
      404:
        description: Not found
      500:
        description: Delete failed
    """
    shipment = query_db(
        "SELECT * FROM Shipments WHERE id=?",
        (id,),
        one=True
    )

    if not shipment:
        abort(404, "Shipment not found")

    # FIX: không cho xoá nếu đã giao
    if shipment['status'] == "DELIVERED":
        abort(400, "Cannot delete delivered shipment")

    success = execute_db(
        "DELETE FROM Shipments WHERE id=?",
        (id,)
    )

    return jsonify({
        "success": True,
        "data": "Shipment deleted"
    })


@logistics_bp.route('/shipments/<int:id>', methods=['GET'])
def get_shipment_by_id(id):
    """
    Get shipment by ID
    ---
    tags:
      - Shipments
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: ID của shipment cần tìm
        example: 1
    responses:
      200:
        description: Thông tin chi tiết shipment
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                transfer_id:
                  type: integer
                  example: 3
                driver_name:
                  type: string
                  example: "Nguyen Van A"
                license_plate:
                  type: string
                  example: "51A-12345"
                status:
                  type: string
                  example: "SHIPPING"
                expected_delivery_at:
                  type: string
                  example: "2026-03-26T10:00:00"
                actual_delivery_at:
                  type: string
                  example: null
      404:
        description: Không tìm thấy shipment với ID này
    """
    shipment = query_db(
        "SELECT * FROM Shipments WHERE id=?",
        (id,),
        one=True
    )

    if not shipment:
        abort(404, "Shipment not found")

    return jsonify({
        "success": True,
        "data": dict(shipment)
    })
