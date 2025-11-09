from flask import Flask, jsonify, request
app = Flask(__name__)

# temporary database
database = {
    "requests": [],
    "next_id": 1
}

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/sms-inbound", methods=['POST'])
def sms_inbound():
    """
    The endpoint Twilio sends all incoming texts to.
    """
    # You'll add your logic here to process the incoming SMS from Twilio.
    # For example, parsing the message and creating a new refill request.
    accepted_medications = ["lisinopril", "metformin"]

    patient_phone = request.form.get('From')
    # should look up the patient name based on phone number from database
    message_body = request.form.get('Body')


    for med in accepted_medications:
        if med in message_body.lower():
            # include patient name as well once you add the database
            new_request = {
                "id": database["next_id"],
                "patient_phone": patient_phone,
                "medication": med,
                "status": "pending"
            }
            database["requests"].append(new_request)
            database["next_id"] += 1
            print(f"New refill request created: {new_request}")
            break


    print(f"Incoming message from {request.form.get('From')}: {request.form.get('Body')}")
    return "SMS received successfully!", 200

@app.route("/api/requests", methods=['GET'])
def get_requests():
    """
    The endpoint your Physician Dashboard calls to get the list of pending refills.
    """
    # In a real application, you would fetch this data from a database.

    """dummy_requests = [
        {"id": 1, "patient": "John Doe", "medication": "Lisinopril 10mg", "status": "pending"},
        {"id": 2, "patient": "Jane Smith", "medication": "Metformin 500mg", "status": "pending"},
    ]
    return jsonify(dummy_requests)"""

    pending = [req for req in database["requests"] if req["status"] == "pending"]
    return jsonify(pending)

# From physician to website
@app.route("/api/approve/<int:id>", methods=['POST'])
def approve_request(id):
    for req in database["requests"]:
        if req["id"] == id:
            req["status"] = "approved"
            print(f"Request with ID {id} has been approved.")
            return jsonify({"status": "success", "message": f"Request {id} approved."})
        
    # if no matching ID found
    return jsonify({"status": "error", "message": f"Request {id} not found."}), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")