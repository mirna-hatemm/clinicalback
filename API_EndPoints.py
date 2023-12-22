
from flask import Flask, request, jsonify ,abort
from UserAuthentication  import signup, login
from Reservations import book_slot, CancelSlot, viewAvailableSlots, viewPatientReservations, updateAppointment , set_schedule
import logging
from flask_cors import CORS
from flask_cors import cross_origin
import os
app = Flask(__name__)

CORS(app, supports_credentials=True)

#defult values if not set in env
app_host = os.getenv('APP_HOST', '0.0.0.0')
app_port = int(os.getenv('APP_PORT', '5000'))
print(f"Starting server at {app_host}:{app_port}")


@app.route('/signup', methods=['POST'])
@cross_origin()
def api_signup():
    data = request.json
    result = signup(data['username'], data['password'], data['email'], data['user_type'])
    return jsonify({'message': result})

@app.route('/login', methods=['POST'])
@cross_origin()
def api_login():
    data = request.json
    message, status_code = login(data['username'], data['password'], data['user_type'])

    # Debug: print the type and value of result
    print("Type of result:", type(message))
    print("Value of result:", message)

    return jsonify({'message': message}), status_code


@app.route('/setSchedule', methods=['POST'])
@cross_origin()
def api_set_schedule():
    try:
        data = request.get_json()

        doctor_username = data['doctor_username']
        reservation_date = data['reservation_date']
        reservation_time = data['reservation_time']
        reservation_endtime = data['reservation_endtime']

        message = set_schedule(doctor_username, reservation_date, reservation_time, reservation_endtime)
        return jsonify({'message': message}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/book_slot', methods=['POST'])
@cross_origin()
def api_book_slot():
    data = request.json
    result = book_slot(data['patient_username'], data['reservation_id'])
    return jsonify({'message': result})

@app.route('/cancel_slot', methods=['POST'])
@cross_origin()
def api_cancel_slot():
    data = request.json
    result = CancelSlot(data['patient_username'], data['reservation_id'])
    return jsonify({'message': result})

@app.route('/viewAvailableSlots', methods=['GET'])
@cross_origin()
def get_available_slots():
    doctor_username = request.args.get('doctor_username')
    if doctor_username:
        slots = viewAvailableSlots(doctor_username)
        if slots:
            return jsonify(slots)
        else:
            return jsonify({"error": "Unable to fetch available slots or none available"}), 500
    else:
        return jsonify({"error": "Doctor username is required"}), 400


@app.route('/view_reservations', methods=['GET'])
@cross_origin()
def api_view_reservations():
    patient_username = request.args.get('patient_username')
    result = viewPatientReservations(patient_username)
    return jsonify({'reservations': result})

@app.route('/update_appointment', methods=['POST'])
@cross_origin()
def api_update_appointment():
        data = request.json
        patient_username = data.get('patient_username')
        result = updateAppointment(data['patient_username'])
        return jsonify({'message': result})

if __name__ == '__main__':
    app.run(host=app_host, port=app_port)

