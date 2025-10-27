import os
import json
import random
import string
from flask import Flask, request, render_template, redirect, url_for, flash
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DECRYPTED_FOLDER'] = 'static/decrypted_images'
app.config['SECRET_KEY'] = 'your_secret_key'
KEY_FILE = 'key.json'

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
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    """عرض الصور المشفرة"""
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.enc')]
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

    flash("Image encrypted successfully!")
    return redirect(url_for('gallery'))


@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt_page():
    """Decrypt encrypted images"""
    encrypted_folder = app.config['UPLOAD_FOLDER']
    decrypted_folder = app.config['DECRYPTED_FOLDER']
    key_file = KEY_FILE
    encrypted_files = [f for f in os.listdir(encrypted_folder) if f.endswith('.enc')]
    decrypted_image = None
    error = None

    if request.method == 'POST':
        filename = request.form['filename']
        password = request.form['password']
        encrypted_path = os.path.join(encrypted_folder, filename)
        decrypted_path = os.path.join(decrypted_folder, filename.replace('.enc', ''))

        # Ensure key.json exists
        if not os.path.exists(key_file):
            with open(key_file, 'w') as f:
                json.dump({}, f)

        with open(key_file, 'r') as f:
            key_data = json.load(f)

        file_data = key_data.get(filename)

        if file_data and password == file_data.get('password'):
            key_hex = file_data.get('key')
            key = bytes.fromhex(key_hex)

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


if __name__ == '__main__':
    app.run(debug=True, port=5001)

