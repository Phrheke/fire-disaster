from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
import os
import datetime
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize the Flask application
app = Flask(__name__)

# Configure application
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize SQLite database connection
conn = sqlite3.connect('alerts.db', check_same_thread=False)
db = conn.cursor()

# Function to add a column if it doesn't already exist
def add_column_if_not_exists(table_name, column_name, column_type):
    db.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in db.fetchall()]
    if column_name not in columns:
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
        conn.commit()

# Update the database to add the `image_path` column if it doesn't exist
@app.route("/updatedb")
def updatedb():
    try:
        add_column_if_not_exists("commonalerts", "image_path", "TEXT")
        add_column_if_not_exists("govtalerts", "image_path", "TEXT")
        return "Database updated successfully."
    except Exception as e:
        return f"An error occurred: {e}"

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def menu():
    return render_template("menu.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/commonalerts", methods=["GET", "POST"])
def commonalerts():
    if request.method == "POST":
        if not request.form.get("calamity"):
            return jsonify({"message": "Must select the fire incident type."}), 400
        elif not request.form.get("location"):
            return jsonify({"message": "Must enter the location."}), 400

        incident = request.form.get("calamity")
        location = request.form.get("location")
        description = request.form.get("description")
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename

        db.execute("INSERT INTO commonalerts (incident, location, description, datetime, image_path) VALUES (?, ?, ?, ?, ?)",
                   (incident, location, description, timestamp, image_path))
        conn.commit()
        return jsonify({"message": "Alert Issued Successfully."}), 200
    else:
        return render_template("alerts.html")

@app.route("/getcommonalerts")
def getcommonalerts():
    alerts = []
    rows = db.execute("SELECT * FROM commonalerts ORDER BY id DESC")
    for row in rows:
        alert = {"datetime": row[1], "location": row[3], "calamity": row[2], "description": row[4], "incident": row[5], "image_path": row[6]}
        alerts.append(alert)
    return jsonify(alerts)

@app.route("/govtalerts", methods=["GET", "POST"])
def govtalerts():
    if request.method == "POST":
        if not request.form.get("username"):
            return jsonify({"message": "Must enter a username."}), 400
        elif not request.form.get("password"):
            return jsonify({"message": "Must enter the password."}), 400
        elif not request.form.get("calamity"):
            return jsonify({"message": "Must select the fire incident type."}), 400
        elif not request.form.get("location"):
            return jsonify({"message": "Must enter the location."}), 400
        elif not request.form.get("description"):
            return jsonify({"message": "Must enter the description."}), 400

        username = request.form.get("username")
        password = request.form.get("password")
        rows = db.execute("SELECT * FROM govtids WHERE username = ?", (username,))
        row = rows.fetchone()
        if row is None or not check_password_hash(row[2], password):
            return jsonify({"message": "Invalid username and/or password."}), 400

        incident = request.form.get("calamity")
        location = request.form.get("location")
        description = request.form.get("description")
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename

        db.execute("INSERT INTO govtalerts (incident, location, description, datetime, image_path) VALUES (?, ?, ?, ?, ?)",
                   (incident, location, description, timestamp, image_path))
        conn.commit()
        return jsonify({"message": "Alert Issued Successfully."}), 200
    else:
        return render_template("govtalerts.html")

@app.route("/getgovtalerts")
def getgovtalerts():
    alerts = []
    rows = db.execute("SELECT * FROM govtalerts ORDER BY id DESC")
    for row in rows:
        alert = {"datetime": row[1], "location": row[3], "calamity": row[2], "description": row[4], "incident": row[5], "image_path": row[6]}
        alerts.append(alert)
    return jsonify(alerts)

@app.route("/generateids")
def generateids():
    usernames = ["fireofficer"]
    passwords = ["admin",]

    for i in range(4):
        db.execute("INSERT INTO govtids (username, password) VALUES (?, ?)", (usernames[i], generate_password_hash(passwords[i])))
        conn.commit()
    return "Government IDs generated successfully."

@app.route("/viewgovtalerts")
def viewgovtalerts():
    alerts = []
    rows = db.execute("SELECT * FROM govtalerts ORDER BY id DESC")
    for row in rows:
        alert = {"datetime": row[1], "location": row[3], "calamity": row[2], "description": row[4], "incident": row[5], "image_path": row[6]}
        alerts.append(alert)
    return render_template("view.html", rows=alerts, alert="Government Issued Alerts")

@app.route("/viewcommonalerts")
def viewcommonalerts():
    alerts = []
    rows = db.execute("SELECT * FROM commonalerts ORDER BY id DESC")
    for row in rows:
        alert = {"datetime": row[1], "location": row[3], "calamity": row[2], "description": row[4], "incident": row[5], "image_path": row[6]}
        alerts.append(alert)
    return render_template("view.html", rows=alerts, alert="Common Alerts")


@app.route("/education")
def education():
    return render_template("education.html")

if __name__ == "__main__":
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(host='0.0.0.0', port=80, debug=True)
