from flask import Blueprint, request, jsonify
from db_helper import get_db_connection

transfer_bp = Blueprint('transfer', __name__)

@transfer_bp.route('/transfers', methods=['POST'])
def create_transfer():
    """
    Create a transfer
    ---
    tags:
      - Transfers
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              source_warehouse:
                type: string
                example: WH1
              destination_warehouse:
                type: string
                example: WH2
              product_id:
                type: integer
                example: 1
              quantity:
                type: integer
                example: 10
    responses:
      201:
        description: Transfer created successfully
      400:
        description: Invalid input
    """

    data = request.json

    source = data.get('source_warehouse')
    destination = data.get('destination_warehouse')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not all([source, destination, product_id, quantity]):
        raise Exception("Missing required fields")

    if quantity <= 0:
        raise Exception("Quantity must be > 0")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check tồn kho nguồn
    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE warehouse = %s AND product_id = %s
    """, (source, product_id))

    result = cursor.fetchone()

    if not result or result['quantity'] < quantity:
        raise Exception("Not enough stock in source warehouse")

    # Trừ kho nguồn
    cursor.execute("""
        UPDATE inventory
        SET quantity = quantity - %s
        WHERE warehouse = %s AND product_id = %s
    """, (quantity, source, product_id))

    # Cộng kho đích
    cursor.execute("""
        INSERT INTO inventory (warehouse, product_id, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + %s
    """, (destination, product_id, quantity, quantity))

    # Tạo transfer
    cursor.execute("""
        INSERT INTO transfers (source, destination, product_id, quantity, status)
        VALUES (%s, %s, %s, %s, 'completed')
    """, (source, destination, product_id, quantity))

    conn.commit()

    return jsonify({'message': 'Transfer created successfully'}), 201

@transfer_bp.route('/transfers', methods=['GET'])
def get_transfers():
    """
    Get all transfers
    ---
    tags:
      - Transfers
    responses:
      200:
        description: List of transfers
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM transfers ORDER BY id DESC")
    data = cursor.fetchall()

    return jsonify(data), 200


@transfer_bp.route('/transfers/suggest', methods=['GET'])
def suggest_warehouse():
    """
    Suggest warehouse for transfer
    ---
    tags:
      - Transfers
    parameters:
      - name: product_id
        in: query
        required: true
        schema:
          type: integer
        example: 1
      - name: quantity
        in: query
        required: true
        schema:
          type: integer
        example: 10
    responses:
      200:
        description: Suggested warehouses
      404:
        description: No warehouse found
    """

    product_id = request.args.get('product_id')
    required_qty = request.args.get('quantity', type=int)

    if not product_id or not required_qty:
        raise Exception("Missing product_id or quantity")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT warehouse, quantity
        FROM inventory
        WHERE product_id = %s AND quantity >= %s
        ORDER BY quantity DESC
    """, (product_id, required_qty))

    results = cursor.fetchall()

    if not results:
        return jsonify({'message': 'No warehouse can fulfill this request'}), 404

    return jsonify({'suggestions': results}), 200