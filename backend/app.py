from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = 'refill_requests.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                doctor_id INTEGER,
                prescription TEXT,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            );
        ''')
        db.commit()

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

    patient_phone = request.form.get('From', '')
    message_body = request.form.get('Body', '')

    for med in accepted_medications:
        if med in message_body.lower():
            try:
                db = get_db()
                cursor = db.cursor()
                # In a real app, you'd look up the patient name from the patients table
                # For now, we can use a placeholder or derive from the phone number
                patient_name = f"Patient ({patient_phone[-4:]})"
                cursor.execute(
                    "INSERT INTO requests (patient_phone, patient_name, medication) VALUES (?, ?, ?)",
                    (patient_phone, patient_name, med)
                )
                db.commit()
                print(f"New refill request for {med} from {patient_phone} created.")
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return "Error processing request", 500
            break


    print(f"Incoming message from {request.form.get('From')}: {request.form.get('Body')}")
    return "SMS received successfully!", 200

@app.route("/api/requests", methods=['GET'])
def get_requests():
    """
    The endpoint your Physician Dashboard calls to get the list of pending refills.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, patient_name as patient, medication, status FROM requests WHERE status = 'pending'")
    rows = cursor.fetchall()
    # Convert rows to a list of dictionaries
    pending_requests = [dict(row) for row in rows]
    return jsonify(pending_requests)

# From physician to website
@app.route("/api/approve/<int:id>", methods=['POST'])
def approve_request(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE requests SET status = 'approved' WHERE id = ?", (id,))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"status": "error", "message": f"Request {id} not found."}), 404
    
    print(f"Request with ID {id} has been approved.")
    return jsonify({"status": "success", "message": f"Request {id} approved."})

if __name__ == "__main__":
    # Initialize the database and create tables if they don't exist
    init_db()
    app.run(debug=True, host="0.0.0.0")