from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "game.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS players_online (
            username TEXT PRIMARY KEY,
            x REAL,
            y REAL,
            z REAL,
            last_update TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now().isoformat()),
        )
        conn.commit()
        return jsonify({"success": True, "message": "Account created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Username already exists"}), 400
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password)),
    )
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"success": True, "message": "Login successful", "username": username}), 200
    return jsonify({"success": False, "error": "Invalid username or password"}), 401


@app.route("/players", methods=["GET"])
def get_players():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username, x, y, z FROM players_online")
    rows = c.fetchall()
    conn.close()

    players = []
    for row in rows:
        username, x, y, z = row
        players.append({
            "username": username,
            "x": x,
            "y": y,
            "z": z,
        })

    return jsonify({"players": players}), 200


@app.route("/update_position", methods=["POST"])
def update_position():
    data = request.get_json()
    username = data.get("username", "").strip()
    x = data.get("x")
    y = data.get("y")
    z = data.get("z")

    if not username:
        return jsonify({"success": False, "error": "Username required"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO players_online (username, x, y, z, last_update)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(username)
        DO UPDATE SET x = excluded.x, y = excluded.y, z = excluded.z, last_update = excluded.last_update
        """,
        (username, x, y, z, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


@app.route("/logout", methods=["POST"])
def logout():
    data = request.get_json()
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"success": False, "error": "Username required"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM players_online WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)