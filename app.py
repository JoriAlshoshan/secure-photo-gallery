import os
import json
import random
import string
import sqlite3
import re
from flask import Flask, request, render_template, redirect, url_for, flash , session
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DECRYPTED_FOLDER'] = 'static/decrypted_images'
app.config['SECRET_KEY'] = 'your_secret_key'
KEY_FILE = 'key.json'


#SQLite database:
con=sqlite3.connect("database.db")
#create users table if doesn't exist
con.execute("create table if not exists users(pid integer primary key,name text,email text, password text)")
#create images table if doesn't exist
con.execute("create table if not exists images(id integer primary key,user_id integer,filename text,key text,password text,foreign key(user_id) references users(pid))")
con.close()

# تأكد من وجود المجلدات
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DECRYPTED_FOLDER'], exist_ok=True)

# تأكد من وجود ملف المفاتيح
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'w') as f:
        json.dump({}, f)

# توليد كلمة مرور عشوائية
def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('decoy.html')

    
@app.route('/login', methods=['GET','POST'])
def login():
    """for login"""
    if request.method=='POST':
        name=request.form['username']
        password=request.form['password']
        con=sqlite3.connect("database.db")
        con.row_factory=sqlite3.Row
        cur=con.cursor()
        cur.execute("select * from users where name=?", (name,))
        data=cur.fetchone()
        con.close()

        if data and check_password_hash(data["password"], password):
            session["user_id"]=data["pid"]
            session["username"]=data["name"]
            return redirect(url_for("gallery"))
        else:
            flash("Invalid username or password, please try again.", "danger")
    return render_template('loginpage.html')

@app.route('/register', methods=['GET','POST'])
def register():
    """rigester page to create account for new users"""
    if request.method=='POST':
        try:
            name=request.form['username']
            email=request.form['email']
            password=request.form['password']
            
            #for password validation
            password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$'
            if not re.match(password_regex, password):
                flash("Password must be 8-20 characters, include uppercase, lowercase, number, and special character.", "danger")
                return redirect(url_for("register"))

            #connect to DB
            con=sqlite3.connect("database.db")
            cur=con.cursor()

            # Check if username already exists
            cur.execute("select * from users where name = ?", (name,))
            if cur.fetchone():
                flash("Username already taken. Please choose another.", "danger")
                return redirect(url_for("register"))

            #hasing the passwords
            hashed_password = generate_password_hash(password)
            #insert values in DB
            cur.execute("INSERT INTO users(name,email,password) VALUES (?,?,?)", (name,email,hashed_password))
            con.commit()
            flash("Record Added  Successfully", "success")
        except:
            flash("Error in Insert Operation: ", "danger")

        finally:
            return redirect(url_for("login"))
            con.close()

    return render_template('register.html')

#@app.route('/gallery')
#def gallery():
#    """عرض الصور المشفرة"""
#    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.enc')]
#    return render_template('gallery.html', uploaded_files=files, logo_image='logo.png')

@app.route('/gallery')
def gallery():
    """عرض الصور المشفرة"""
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
    """رفع الصورة وتشفيرها"""
    if request.method == 'GET':
        return render_template('upload.html')

    if 'image' not in request.files:
        flash("لم يتم اختيار ملف.")
        return redirect(url_for('gallery'))

    file = request.files['image']
    if file.filename == '':
        flash("الرجاء اختيار ملف صالح.")
        return redirect(url_for('gallery'))

    data = file.read()

    # توليد مفتاح تشفير جديد
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    # حفظ الملف المشفر
    enc_filename = file.filename + '.enc'
    enc_path = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
    with open(enc_path, 'wb') as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    # إنشاء كلمة مرور عشوائية وربطها مع المفتاح
    password = generate_password()
    key_hex = key.hex()

    # تحديث ملف المفاتيح
    with open(KEY_FILE, 'r') as f:
        key_data = json.load(f)

    key_data[enc_filename] = {
        "key": key_hex,
        "password": password
    }

    with open(KEY_FILE, 'w') as f:
        json.dump(key_data, f, indent=4)


    # Save image details in DB
    user_id = session.get("user_id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("Insert into images(user_id, filename, key, password) VALUES (?, ?, ?, ?)", (user_id, enc_filename, key_hex, password))
    con.commit()
    con.close()
    flash("Image encrypted successfully!")
    return redirect(url_for('gallery'))


@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt_page():
    """Decrypt encrypted images"""
    encrypted_folder = app.config['UPLOAD_FOLDER']
    decrypted_folder = app.config['DECRYPTED_FOLDER']
    key_file = KEY_FILE
    encrypted_files = [f for f in os.listdir(encrypted_folder) if f.endswith('.enc')]
    user_id = session.get("user_id")
    decrypted_image = None
    error = None

    #to show images of the user
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select filename from images where user_id=?", (user_id,))
    encrypted_files = [row["filename"] for row in cur.fetchall()]
    con.close()
    
    if request.method == 'POST':
        filename = request.form['filename']
        password = request.form['password']

        # Ensure key.json exists
        #if not os.path.exists(key_file):
        #    with open(key_file, 'w') as f:
        #        json.dump({}, f)
        #with open(key_file, 'r') as f:
        #    key_data = json.load(f)
        #file_data = key_data.get(filename)
        #if file_data and password == file_data.get('password'):
        #    key_hex = file_data.get('key')
        #    key = bytes.fromhex(key_hex)

        #get key and password from DB for the user
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("select key, password from images where filename=? and user_id=?", (filename, user_id))
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
                flash("✅ Image decrypted successfully!")
            except Exception as e:
                error = "❌ Failed to decrypt the image. The key or file may be incorrect."
        else:
            error = "❌ Incorrect password!"

    return render_template(
        'decrypt.html',
        encrypted_files=encrypted_files,
        decrypted_image=decrypted_image,
        error=error
    )

@app.route('/logout')
def logout():
    """logout to end the session"""
    session.clear()
    return redirect(url_for("index"))



if __name__ == '__main__':
    app.run(debug=True, port=5001)

