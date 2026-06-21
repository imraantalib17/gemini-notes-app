from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from google import genai

app = Flask(__name__)
# A secure key to keep your login sessions private
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-notebook-key")

# Grab your Gemini API Key from the Codespace secrets environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def init_db():
    """Creates a secure SQL database file inside your server if it doesn't exist yet"""
    conn = sqlite3.connect("notebook.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS notes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       content TEXT, 
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('notebook.html')

@app.route('/login', methods=['POST'])
def login():
    # 🔐 CHANGE 'password123' TO YOUR OWN PRIVATE PASSWORD LATER!
    if request.form.get('password') == 'password123':
        session['logged_in'] = True
        return redirect(url_for('home'))
    return "Incorrect password! Go back and try again.", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/get_notes', methods=['GET'])
def get_notes():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    conn = sqlite3.connect("notebook.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM notes ORDER BY timestamp DESC")
    notes = [{"id": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(notes)

@app.route('/save_note', methods=['POST'])
def save_note():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    conn = sqlite3.connect("notebook.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (content) VALUES (?)", (data['content'],))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if not GEMINI_API_KEY: return jsonify({"error": "Gemini API key is missing on the server!"}), 500
    
    data = request.json
    prompt_text = data.get('prompt', '')
    
    try:
        # Initialize the modern Google GenAI SDK client
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_text,
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    # Runs the server internally on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
