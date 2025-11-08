from flask import Flask, jsonify, request
app = Flask(__name__)

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
    print(f"Incoming message from {request.form.get('From')}: {request.form.get('Body')}")
    return "SMS received successfully!", 200

@app.route("/api/requests", methods=['GET'])
def get_requests():
    """
    The endpoint your Physician Dashboard calls to get the list of pending refills.
    """
    # In a real application, you would fetch this data from a database.
    dummy_requests = [
        {"id": 1, "patient": "John Doe", "medication": "Lisinopril 10mg", "status": "pending"},
        {"id": 2, "patient": "Jane Smith", "medication": "Metformin 500mg", "status": "pending"},
    ]
    return jsonify(dummy_requests)

@app.route("/api/approve/<int:id>", methods=['POST'])
def approve_request(id):
    print(f"Request with ID {id} has been approved.")
    return jsonify({"status": "success", "message": f"Request {id} approved."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")