import sqlite3
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS  # <-- Import CORS
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
from dotenv import load_dotenv

# --- 1. Setup & Config ---
load_dotenv()
app = Flask(__name__)
# This allows your React app at localhost:5173 to talk to your Flask app
CORS(app) 
DATABASE = 'refill_requests.db'

# --- Twilio Config ---
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("Twilio Client initialized.")
except Exception as e:
    print(f"Error initializing Twilio Client: {e}")
    twilio_client = None

# --- 2. Bot "Brain": Question Flow ---
# This dictionary drives the entire bot conversation
MEDICATION_QUESTIONS = {
    'lisinopril': [
        {'key': 'sideEffects', 'question': 'Any new side effects? (e.g., cough, dizziness)'},
        {'key': 'bloodPressure', 'question': 'What is your last home blood pressure reading? (e.g., 125/80)'}
    ],
    'metformin': [
        {'key': 'sideEffects', 'question': 'Any new side effects? (e.g., nausea, stomach upset)'},
        {'key': 'bloodSugar', 'question': 'What are your recent morning blood sugar readings?'}
    ],
    'default': [
        {'key': 'sideEffects', 'question': 'Any new side effects?'}
    ]
}

# --- 3. Database Functions ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with all necessary tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.executescript('''
            -- Stores known patients
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL
            );

            -- Stores *completed* requests for the doctor's dashboard
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_phone TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                medication TEXT NOT NULL,
                answers_json TEXT NOT NULL, -- Stores answers as a JSON string
                status TEXT NOT NULL DEFAULT 'pending' 
            );

            -- Stores *active, in-progress* bot conversations
            CREATE TABLE IF NOT EXISTS conversations (
                patient_phone TEXT PRIMARY KEY NOT NULL,
                current_step TEXT NOT NULL, -- The 'key' of the question we just asked
                medication TEXT NOT NULL,
                answers_json TEXT NOT NULL  -- Stores answers as we get them
            );

            -- Stores dashboard users (doctors, admins)
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            );
            
            -- Add a mock patient for testing
            INSERT OR IGNORE INTO patients (name, phone) VALUES ('Jane Doe', '+15551234567');
            INSERT OR IGNORE INTO patients (name, phone) VALUES ('John Smith', '+15557654321');

            -- Add mock users for testing (password: "password")
            INSERT OR IGNORE INTO users (email, password_hash, role) VALUES ('admin@example.com', 'pbkdf2:sha256:600000$V1i3I9k5jL3xG9pG$c799c8b7623d4055c953a8158a2f4e55b610b83945b6f183bff46344d34b8c3a', 'admin');
            INSERT OR IGNORE INTO users (email, password_hash, role) VALUES ('user@example.com', 'pbkdf2:sha256:600000$V1i3I9k5jL3xG9pG$c799c8b7623d4055c953a8158a2f4e55b610b83945b6f183bff46344d34b8c3a', 'user');

        ''')
        print("Database initialized.")
        db.commit()

# --- 4. Twilio Webhook (The Bot "Brain") ---
@app.route("/sms-inbound", methods=['POST'])
def sms_inbound():
    """
    This is the main bot logic that handles all incoming texts.
    It's "stateful" - it remembers where it left off.
    """
    patient_phone = request.form['From']
    patient_message = request.form['Body'].strip()
    twiml_response = MessagingResponse()

    conn = get_db()
    cursor = conn.cursor()

    # 1. Identify the patient
    cursor.execute("SELECT name FROM patients WHERE phone = ?", (patient_phone,))
    patient_row = cursor.fetchone()
    
    if not patient_row:
        twiml_response.message("Sorry, your phone number is not recognized. Please call the office.")
        conn.close()
        return str(twiml_response)
    
    patient_name = patient_row['name']

    # 2. Check for an active conversation
    cursor.execute("SELECT * FROM conversations WHERE patient_phone = ?", (patient_phone,))
    conversation = cursor.fetchone()

    if not conversation:
        # --- This is a NEW request ---
        message_lower = patient_message.lower()
        med_name = None
        
        if 'lisinopril' in message_lower:
            med_name = 'lisinopril'
        elif 'metformin' in message_lower:
            med_name = 'metformin'
        # Add other meds here...

        if not med_name:
            twiml_response.message(f"Hi {patient_name}. Please text 'refill' and your medication name (e.g., 'refill lisinopril').")
            conn.close()
            return str(twiml_response)

        # Start the conversation!
        questions = MEDICATION_QUESTIONS.get(med_name, MEDICATION_QUESTIONS['default'])
        first_question = questions[0]

        cursor.execute(
            "INSERT INTO conversations (patient_phone, current_step, medication, answers_json) VALUES (?, ?, ?, ?)",
            (patient_phone, first_question['key'], med_name, json.dumps({}))
        )
        twiml_response.message(f"Hi {patient_name}. To refill your {med_name}, I just need a few answers. {first_question['question']}")

    else:
        # --- This is an ANSWER to a previous question ---
        med_name = conversation['medication']
        current_step_key = conversation['current_step']
        answers = json.loads(conversation['answers_json'])
        
        # Save the answer
        answers[current_step_key] = patient_message
        
        # Find the next question
        questions = MEDICATION_QUESTIONS.get(med_name, MEDICATION_QUESTIONS['default'])
        current_index = next((i for i, q in enumerate(questions) if q['key'] == current_step_key), -1)
        
        next_index = current_index + 1
        
        if next_index < len(questions):
            # --- There are MORE questions ---
            next_question = questions[next_index]
            cursor.execute(
                "UPDATE conversations SET current_step = ?, answers_json = ? WHERE patient_phone = ?",
                (next_question['key'], json.dumps(answers), patient_phone)
            )
            twiml_response.message(next_question['question'])
        
        else:
            # --- This is the FINAL answer ---
            # 1. Create the final request for the doctor
            cursor.execute(
                "INSERT INTO requests (patient_phone, patient_name, medication, answers_json, status) VALUES (?, ?, ?, ?, ?)",
                (patient_phone, patient_name, med_name, json.dumps(answers), 'pending')
            )
            # 2. Delete the active conversation
            cursor.execute("DELETE FROM conversations WHERE patient_phone = ?", (patient_phone,))
            
            # 3. Tell the patient we're done
            twiml_response.message("Thanks! I've sent your request with all your answers to the doctor for review.")

    # Commit changes and send the TwiML reply
    conn.commit()
    conn.close()
    return str(twiml_response)

# --- 5. API Routes for React Dashboard ---

@app.route("/api/login", methods=['POST'])
def login_user():
    """
    Handles user login for the React dashboard.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # In a real app, you would return a session token (e.g., JWT) here
    # For now, a success message is sufficient for navigation.
    return jsonify({"message": "Login successful", "role": user['role']})


@app.route("/api/pending-requests", methods=['GET'])
def get_pending_requests():
    """
    Called by the React dashboard to get all pending refills.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM requests WHERE status = 'pending' ORDER BY id")
    rows = cursor.fetchall()
    
    pending_list = []
    for row in rows:
        req = dict(row)
        # Convert the JSON string back into an object for React
        req['answers'] = json.loads(req['answers_json'])
        del req['answers_json'] # Clean up
        
        # Rename keys to match React's camelCase preference
        req['patientPhone'] = req.pop('patient_phone')
        req['patientName'] = req.pop('patient_name')
        
        pending_list.append(req)
        
    return jsonify(pending_list)

@app.route("/api/request/approve/<int:request_id>", methods=['POST'])
def approve_request(request_id):
    """
    Called by the React "Approve" button.
    Updates the request and sends a confirmation SMS.
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT patient_phone, medication FROM requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    
    if not req:
        return jsonify({"error": "Request not found"}), 404

    patient_phone, medication = req['patient_phone'], req['medication']

    cursor.execute("UPDATE requests SET status = 'approved' WHERE id = ?", (request_id,))
    db.commit()

    # --- Send Twilio Confirmation SMS ---
    try:
        message_body = f"Your refill request for {medication} has been approved by your doctor."
        message = twilio_client.messages.create(
            to=patient_phone,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        print(f"Approval SMS sent: {message.sid}")
    except Exception as e:
        print(f"Error sending approval SMS: {e}")

    return jsonify({"message": f"Request {request_id} approved."})

@app.route("/api/request/deny/<int:request_id>", methods=['POST'])
def deny_request(request_id):
    """
    Called by the React "Deny" button.
    Updates the request and sends a "book appointment" SMS.
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT patient_phone FROM requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    
    if not req:
        return jsonify({"error": "Request not found"}), 404

    patient_phone = req['patient_phone']
    
    cursor.execute("UPDATE requests SET status = 'denied' WHERE id = ?", (request_id,))
    db.commit()

    # --- Send Twilio "Book Appointment" SMS ---
    try:
        message_body = "Your doctor has reviewed your refill request. Please call the office to book an appointment."
        message = twilio_client.messages.create(
            to=patient_phone,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        print(f"Denial SMS sent: {message.sid}")
    except Exception as e:
        print(f"Error sending denial SMS: {e}")

    return jsonify({"message": f"Request {request_id} denied."})

# --- 6. Run the App ---
if __name__ == "__main__":
    init_db()  # Initialize the database on startup
    # Host="0.0.0.0" makes it accessible on your network (for ngrok)
    app.run(debug=True, host="0.0.0.0", port=5000)