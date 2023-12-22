import logging

from database import get_cursor, commit

def isbooked(reservation_id):
    cursor = get_cursor()
    cursor.execute("SELECT isBooked FROM reservations WHERE reservationID = %s", (reservation_id,))
    is_booked = cursor.fetchone()
    return is_booked and is_booked[0]

def ispatient(username):
    cursor = get_cursor()
    cursor.execute("SELECT * FROM patientsdata WHERE Username = %s", (username,))
    return bool(cursor.fetchone())


def outputformat(reservations, include_doctor=False):
    readable_output = []

    for reservation in reservations:
        if include_doctor:
            reservation_id, doctor_username, date, start_time, end_time = reservation
        else:
            reservation_id, date, start_time, end_time = reservation

        # Check if start_time and end_time are tuples and convert accordingly
        if isinstance(start_time, tuple):
            start_h, start_m = start_time
        else:  # Assuming start_time is a timedelta object
            start_h, start_m = divmod(start_time.seconds, 3600)
            start_m //= 60

        if isinstance(end_time, tuple):
            end_h, end_m = end_time
        else:  # Assuming end_time is a timedelta object
            end_h, end_m = divmod(end_time.seconds, 3600)
            end_m //= 60

        # Format the output string
        if include_doctor:
            readable_output.append(
                f"ID: {reservation_id}, Doctor: {doctor_username}, Date: {date}, Time: {start_h}:{start_m:02} - {end_h}:{end_m:02}")
        else:
            readable_output.append(
                f"ID: {reservation_id}, Date: {date}, Time: {start_h}:{start_m:02} - {end_h}:{end_m:02}")

    return readable_output


def set_schedule(doctor_username, reservation_date, reservation_time, reservation_endtime,is_booked=False):
    cursor = get_cursor()

    # Check if the user is a doctor
    cursor.execute("SELECT * FROM doctorsdata WHERE Username = %s", (doctor_username,))
    user = cursor.fetchone()

    if not user:
        return "Only doctors are allowed to set schedules!"


    cursor.execute(
        """
        INSERT INTO reservations (reservationDate, reservationTime, doctorUsername, reservationEndtime,isBooked)
        VALUES (%s, %s, %s, %s ,%s)
        """,
        (reservation_date, reservation_time, doctor_username,  reservation_endtime,is_booked)
    )

    commit()
    return "Schedule set successfully!"


def viewAvailableSlots(doctor_username):
    cursor = get_cursor()
    try:
        cursor.execute(
            """
            SELECT reservationID, reservationDate, reservationTime, reservationEndtime
            FROM reservations
            WHERE doctorUsername = %s AND isBooked = False
            ORDER BY reservationDate, reservationTime
            """,
            (doctor_username,)
        )

        available_slots = cursor.fetchall()
        if not available_slots:
            return ["No available slots for this doctor."]

        # Convert the fetched slots into a more readable format
        slots_formatted = []
        for slot in available_slots:
            reservation_id, reservation_date, reservation_time, reservation_endtime = slot
            slot_dict = {
                'reservationID': reservation_id,
                'doctorUsername': doctor_username,
                'reservationDate': reservation_date.strftime('%Y-%m-%d'),  # Format date
                'reservationTime': (reservation_time.seconds//3600, reservation_time.seconds//60%60),  # Convert timedelta to hours and minutes
                'reservationEndtime': (reservation_endtime.seconds//3600, reservation_endtime.seconds//60%60),  # Convert timedelta to hours and minutes
            }
            slots_formatted.append(slot_dict)

        return slots_formatted
    except Exception as e:
        logging.error(f"Error fetching available slots for doctor {doctor_username}: {e}")
        return None  # You might want to return None or an appropriate message



def book_slot(patient_username, reservation_id):
    cursor = get_cursor()

    if isbooked(reservation_id):
        return "This slot is already booked."

    if not ispatient(patient_username):
        return "Only patients can book slots."
    # Book the slot for the patient
    cursor.execute(
        """
        UPDATE reservations SET isBooked = True, patientUsername = %s 
        WHERE reservationID = %s
        """,
        (patient_username, reservation_id)
    )

    commit()
    return "Slot booked successfully!"





def updateAppointment(patient_username):
    cursor = get_cursor()

    # Display the patient's current appointments
    cursor.execute(
        """
        SELECT reservationID, doctorUsername, reservationDate, reservationTime, reservationEndtime
        FROM reservations
        WHERE patientUsername = %s AND isBooked = True
        """,
        (patient_username,)
    )

    appointments = cursor.fetchall()

    # If the patient has no appointments
    if not appointments:
        return "You have no appointments to update."

    # Print appointments using the outputformat function for consistency
    print("Your appointments:")
    print('\n'.join(outputformat(appointments, include_doctor=True)))

    # Choose appointment to update by ID
    chosen_id = int(input("Enter the ID of the appointment you wish to update: "))

    # Choose to change doctor or slot
    choice = input("Do you want to change the doctor (D) or the slot (S)? ").upper()

    if choice == 'D':
        # Get new doctor's username
        new_doctor = input("Enter new doctor's username: ")

        # Display available slots for the new doctor
        slots = viewAvailableSlots(new_doctor)
        if not slots or isinstance(slots[0], str) and slots[0].startswith("No available slots"):
            return slots[0]

        # Print the available slots using outputformat function for consistency
        print("Available slots:")
        print('\n'.join(outputformat(
            [(slot['reservationID'], slot['reservationDate'], slot['reservationTime'], slot['reservationEndtime']) for slot in slots],
            include_doctor=False
        )))

        # Choose a new slot
        new_slot_id = int(input("Enter the ID of the slot you wish to book: "))

        # Book the new slot using the book_slot function
        booking_status = book_slot(patient_username, new_slot_id)
        if booking_status != "Slot booked successfully!":
            return booking_status

        # Cancel the old reservation now that the new slot is booked
        cancellation_status = CancelSlot(patient_username, chosen_id)
        if cancellation_status != "Slot deleted successfully!":
            return cancellation_status

        return "Appointment updated successfully."

    elif choice == 'S':
        # Fetch the doctor's username for the chosen appointment
        cursor.execute("SELECT doctorUsername FROM reservations WHERE reservationID = %s", (chosen_id,))
        result = cursor.fetchone()
        if result is None:
            return "No appointment found with the given ID."

        doctor_username = result[0]

        # Display available slots for the current doctor
        slots = viewAvailableSlots(doctor_username)
        if not slots or isinstance(slots[0], str) and slots[0].startswith("No available slots"):
            return slots[0]

        # Print the available slots using outputformat function for consistency
        print("Available slots:")
        print('\n'.join(outputformat(
            [(slot['reservationID'], slot['reservationDate'], slot['reservationTime'], slot['reservationEndtime']) for slot in slots],
            include_doctor=False
        )))

        # Choose a new slot
        new_slot_id = int(input("Enter the ID of the slot you wish to book: "))

        # Proceed to update the reservation directly
        # Get details of the new slot
        cursor.execute(
            """
            SELECT reservationDate, reservationTime, reservationEndtime
            FROM reservations
            WHERE reservationID = %s
            """,
            (new_slot_id,)
        )
        new_date, new_time, new_endtime = cursor.fetchone()

        # Mark the old slot as available and update it to the new slot details
        cursor.execute(
            """
            UPDATE reservations
            SET reservationDate = %s, reservationTime = %s, reservationEndtime = %s, isBooked = False, patientUsername = NULL
            WHERE reservationID = %s
            """,
            (new_date, new_time, new_endtime, chosen_id)
        )

        # Mark the new slot as booked by the patient
        cursor.execute(
            """
            UPDATE reservations
            SET isBooked = True, patientUsername = %s
            WHERE reservationID = %s
            """,
            (patient_username, new_slot_id)
        )

        # Assume here we should commit the changes
        commit()

        return "Appointment updated successfully."




def CancelSlot(patient_username, reservation_id):
    cursor = get_cursor()

    if not ispatient(patient_username):
        return "Only patients can cancel slots."

    if not isbooked(reservation_id):
        return "No reservations to cancel."

    # Update the slot as unbooked
    cursor.execute(
        """
        UPDATE reservations SET isBooked = false, patientUsername = NULL 
        WHERE reservationID = %s
        """,
        (reservation_id,)
    )

    commit()
    return "Slot deleted successfully!"

def viewPatientReservations(patient_username):
    cursor = get_cursor()

    # Fetch all reservations for a given patient
    cursor.execute(
        """
        SELECT reservationID, doctorUsername, reservationDate, reservationTime, reservationEndtime
        FROM reservations 
        WHERE patientUsername = %s AND isBooked = True
        """,
        (patient_username,)
    )

    reservations = cursor.fetchall()

    if not reservations:
        return ["You have no reservations."]

    return outputformat(reservations, include_doctor=True)

result=viewAvailableSlots("rehab")
print(result)
