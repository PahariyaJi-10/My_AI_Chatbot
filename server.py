import os
import sqlite3
from datetime import datetime
from flask_cors import CORS
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")
client = genai.Client( 
    api_key=api_key
)
app = Flask(__name__)
CORS(app)


chat = client.chats.create(model="gemini-2.5-flash")

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

@app.route("/history", methods=["GET"])
def get_history():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, message, timestamp FROM messages")
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
@app.route("/chat", methods=["POST"])
def chat_api():
    data = request.json
    message = data["message"]

    # Save user message
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (role, message, timestamp) VALUES (?, ?, ?)",
        ("user", message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

    # Send to Gemini
    response = chat.send_message(message)
    bot_reply = response.text

    # Save bot reply
    cursor.execute(
        "INSERT INTO messages (role, message, timestamp) VALUES (?, ?, ?)",
        ("bot", bot_reply, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    print("Starting Flask Server...")
    app.run(debug=True)