import socket
import threading
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime  # Fix datetime import
from flask_cors import CORS

app = Flask(__name__)
DATABASE = 'database.db'
CORS(app)
# Server configuration
SERVER_IP = "192.168.50.31"  # Match this to your local IP
SERVER_PORT = 3000  # Same port as in the Arduino sketch

def init_db():
    """Initialize the SQLite database and create the users table."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            email TEXT NOT NULL UNIQUE,
                            rfid TEXT NOT NULL UNIQUE
                         )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rfid TEXT NOT NULL,
                            name TEXT NOT NULL,
                            timestamp TEXT NOT NULL,
                            message TEXT NOT NULL
                         )''')
     
        # Check if the default user exists before inserting
        cursor.execute("SELECT * FROM users WHERE email = ?", ("D1:9F:32:2",))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (name, email, rfid) VALUES (?, ?, ?)", ("Jonas", "D1:9F:32:2", "D1:9F:32:2"))
            conn.commit()

@app.route('/users', methods=['GET'])
def get_users():
    """Get a list of all users."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return jsonify([{"id": row[0], "name": row[1], "email": row[2], "rfid": row[3]} for row in users])

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
            user_id = cursor.lastrowid
            return jsonify({"id": user_id, "name": name, "email": email}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Email already exists"}), 400

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user's information."""
    data = request.json
    name = data.get('name')
    email = data.get('email')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        cursor.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user_id))
        conn.commit()
        return jsonify({"id": user_id, "name": name, "email": email})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted"})

@app.route('/logs', methods=['POST'])
def create_log():
    data = request.get_json()
    rfid = data.get('rfid')
    name = data.get('name')
    message = data.get('message')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO logs (rfid, name, timestamp, message)
                          VALUES (?, ?, ?, ?)''', (rfid, name, timestamp, message))
        conn.commit()

    return jsonify({'message': 'Log created successfully!'}), 201


def create_log_from_software(rfid, name, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO logs (rfid, name, timestamp, message)
                          VALUES (?, ?, ?, ?)''', (rfid, name, timestamp, message))
        conn.commit()

@app.route('/logs', methods=['GET'])
def get_logs():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs')
        logs = cursor.fetchall()

    logs_list = []
    for log in logs:
        logs_list.append({
            'id': log[0],  # Access tuple by index
            'rfid': log[1],
            'name': log[2],
            'timestamp': log[3],
            'message': log[4]
        })

    return jsonify(logs_list), 200

@app.route('/logs/<int:id>', methods=['GET'])
def get_log(id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs WHERE id = ?', (id,))
        log = cursor.fetchone()

        if log:
            return jsonify({
                'id': log[0],
                'rfid': log[1],
                'name': log[2],
                'timestamp': log[3],
                'message': log[4]
            }), 200
        else:
            return jsonify({'error': 'Log not found'}), 404

@app.route('/logs/<int:id>', methods=['PUT'])
def update_log(id):
    data = request.get_json()
    rfid = data.get('rfid')
    name = data.get('name')
    message = data.get('message')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE logs 
                          SET rfid = ?, name = ?, message = ? 
                          WHERE id = ?''', (rfid, name, message, id))
        conn.commit()

    return jsonify({'message': 'Log updated successfully!'}), 200

@app.route('/logs/<int:id>', methods=['DELETE'])
def delete_log(id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM logs WHERE id = ?', (id,))
        conn.commit()

    return jsonify({'message': 'Log deleted successfully!'}), 200

def start_server():
    """Start the socket server to receive UID from clients."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server started, listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        # Wait for a connection
        print("Waiting for a connection...")
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")

        try:
            # Receive the UID from the client
            data = client_socket.recv(1024).decode('utf-8').strip()
            if data:
                print(f"Received UID: {data}")
                # Check user from database
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE rfid = ?", (data,))
                    user = cursor.fetchone()
                    if user:
                        print(f"User found: {user[1]}")
                        create_log_from_software(data, user[1], "Access granted")
                        response = "User found"
                    else:
                        print("User not found.")
                        create_log_from_software(data, "Unknown card", "Access denied")
                        response = "User not found"
                
                # Send response to the client
                client_socket.sendall(response.encode('utf-8'))
                print(f"Sent response: {response}")
            else:
                print("No data received.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up the connection
            client_socket.close()
            print("Connection closed.")

def start_server_thread():
    """Start the socket server in a separate thread."""
    thread = threading.Thread(target=start_server)
    thread.daemon = True  # Ensures the thread will exit when the main program exits
    thread.start()

if __name__ == "__main__":
    try:
        init_db()
        start_server_thread()  # Start socket server in a separate thread
        app.run(debug=True, use_reloader=False)  # Disable reloader as we already have threading
    except KeyboardInterrupt:
        print("\nServer stopped.")
