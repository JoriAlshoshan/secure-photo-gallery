import os
import json
import random
import string
import sqlite3
import re
from flask import Flask, request, render_template, redirect, url_for, flash, session
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DECRYPTED_FOLDER'] = 'static/decrypted_images'
app.config['SECRET_KEY'] = 'your_secret_key'

#  Mailtrap SMTP Configuration 
SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
SMTP_USERNAME = "1b99eb450eb119"
SMTP_PASSWORD = "cd02f575d364fe"  

# Database Setup 
con = sqlite3.connect("database.db")
con.execute("CREATE TABLE IF NOT EXISTS users(pid INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT, key TEXT, password TEXT, FOREIGN KEY(user_id) REFERENCES users(pid))")
con.close()

# Ensure upload and decrypted folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DECRYPTED_FOLDER'], exist_ok=True)

#  Utility Functions 
def generate_password(length=8):
    """Generate a random password for image encryption"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_email(receiver_email, password):
    """Send the image decryption password to the user's email"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Image Decryption Password"
        msg["From"] = "noreply@safesanit.com"
        msg["To"] = receiver_email

        text = f"Hello,\n\nHere is your image decryption password: {password}\n\nKeep it safe!"
        html = f"""
        <html>
        <body>
            <h3>Your image decryption password:</h3>
            <p><b>{password}</b></p>
            <p>Keep this password safe to decrypt your uploaded image.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print("Failed to send email:", e)

# Routes 
@app.route('/')
def index():
    """Main page"""
    return render_template('decoy.html')

@app.route('/login', methods=['GET','POST'])
def login():
    """User login"""
    if request.method == 'POST':
        name = request.form['username']
        password = request.form['password']

        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE name=?", (name,))
        data = cur.fetchone()
        con.close()

        if data and check_password_hash(data["password"], password):
            session["user_id"] = data["pid"]
            session["username"] = data["name"]
            session["email"] = data["email"]
            return redirect(url_for("gallery"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('loginpage.html')

@app.route('/register', methods=['GET','POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        try:
            name = request.form['username']
            email = request.form['email']
            password = request.form['password']

            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$'
            if not re.match(password_regex, password):
                flash("Password must be 8-20 characters, include uppercase, lowercase, number, and special character.", "danger")
                return redirect(url_for("register"))

            con = sqlite3.connect("database.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE name=?", (name,))
            if cur.fetchone():
                flash("Username already exists.", "danger")
                return redirect(url_for("register"))

            hashed_password = generate_password_hash(password)
            cur.execute("INSERT INTO users(name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            con.commit()
            flash("Registration successful! Please log in.", "success")
        except Exception as e:
            flash(f"Error during registration: {e}", "danger")
        finally:
            con.close()
            return redirect(url_for("login"))
    return render_template('register.html')

@app.route('/gallery')
def gallery():
    """Display user's encrypted images"""
    user_id = session.get("user_id")
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT filename FROM images WHERE user_id=?", (user_id,))
    files = [row["filename"] for row in cur.fetchall()]
    con.close()
    return render_template('gallery.html', uploaded_files=files, logo_image='logo.png')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload and encrypt image, then send decryption password via email"""
    if request.method == 'GET':
        return render_template('upload.html')

    if 'image' not in request.files:
        flash("No file selected.")
        return redirect(url_for('gallery'))

    file = request.files['image']
    if file.filename == '':
        flash("Please select a valid file.")
        return redirect(url_for('gallery'))

    data = file.read()
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    enc_filename = file.filename + '.enc'
    enc_path = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
    with open(enc_path, 'wb') as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    password = generate_password()
    key_hex = key.hex()

    user_id = session.get("user_id")
    user_email = session.get("email")

    # Save image info in database
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO images(user_id, filename, key, password) VALUES (?, ?, ?, ?)", (user_id, enc_filename, key_hex, password))
    con.commit()
    con.close()

    # Send decryption password by email
    send_email(user_email, password)

    flash("Image encrypted successfully! The password has been sent to your email.", "success")
    return redirect(url_for('gallery'))

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt_page():
    """Decrypt selected image"""
    encrypted_folder = app.config['UPLOAD_FOLDER']
    decrypted_folder = app.config['DECRYPTED_FOLDER']
    user_id = session.get("user_id")
    decrypted_image = None
    error = None

    # Get user's images
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT filename FROM images WHERE user_id=?", (user_id,))
    encrypted_files = [row["filename"] for row in cur.fetchall()]
    con.close()
    
    if request.method == 'POST':
        filename = request.form['filename']
        password = request.form['password']

        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT key, password FROM images WHERE filename=? AND user_id=?", (filename, user_id))
        row = cur.fetchone()
        con.close()
        
        if row and password == row["password"]:
            key = bytes.fromhex(row["key"])
            encrypted_path = os.path.join(encrypted_folder, filename)
            decrypted_path = os.path.join(decrypted_folder, filename.replace('.enc', ''))
        
            try:
                with open(encrypted_path, 'rb') as enc_file:
                    nonce = enc_file.read(16)
                    tag = enc_file.read(16)
                    ciphertext = enc_file.read()

                cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
                decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

                with open(decrypted_path, 'wb') as dec_file:
                    dec_file.write(decrypted_data)

                decrypted_image = os.path.basename(decrypted_path)
                flash("Image decrypted successfully!")
            except Exception:
                error = "Decryption failed. Invalid key or file."
        else:
            error = "Incorrect password!"

    return render_template('decrypt.html', encrypted_files=encrypted_files, decrypted_image=decrypted_image, error=error)

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
