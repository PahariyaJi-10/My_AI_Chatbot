import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Create Flask app
app = Flask(__name__)
CORS(app)


# ========================
# DATABASE INITIALIZATION
# ========================
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ========================
# CLEAR CHAT
# ========================
@app.route("/clear", methods=["POST"])
def clear_chat():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"})


# ========================
# GET HISTORY
# ========================
@app.route("/history", methods=["GET"])
def get_history():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, message, timestamp FROM messages ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "role": row[0],
            "message": row[1],
            "timestamp": row[2]
        })

    return jsonify(history)


# ========================
# CHAT API
# ========================
@app.route("/chat", methods=["POST"])
def chat_api():
    data = request.json
    message = data.get("message")

    if not message:
        return jsonify({"reply": "No message received"}), 400

    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()

    # Save user message
    cursor.execute(
        "INSERT INTO messages (role, message, timestamp) VALUES (?, ?, ?)",
        ("user", message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

    # Send to Gemini
    try:
        response = model.generate_content(message)
        bot_reply = response.text
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    # Save bot reply
    cursor.execute(
        "INSERT INTO messages (role, message, timestamp) VALUES (?, ?, ?)",
        ("bot", bot_reply, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": bot_reply})


# ========================
# RUN SERVER
# ========================
if __name__ == "__main__":
    print("Starting Flask Server...")
    app.run(host="0.0.0.0", port=5000)