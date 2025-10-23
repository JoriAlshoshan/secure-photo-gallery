import os
import json
from flask import Flask, request, render_template, redirect, url_for, flash
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your_secret_key'
KEY_STORE = 'keys.json'  # JSON file to store encryption keys

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Create keys.json file if it doesn't exist
if not os.path.exists(KEY_STORE):
    with open(KEY_STORE, 'w') as f:
        json.dump({}, f)

def save_key(filename, key_hex):
    """Save the encryption key for each file in keys.json"""
    with open(KEY_STORE, 'r') as f:
        keys = json.load(f)
    keys[filename] = key_hex
    with open(KEY_STORE, 'w') as f:
        json.dump(keys, f, indent=4)

@app.route('/')
def index():
    """Redirect root URL to the gallery page"""
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    """Display the gallery page showing encrypted files"""
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if not f.startswith('.')]
    return render_template('gallery.html', uploaded_files=files, logo_image='logo.png')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle image upload and encryption"""
    if request.method == 'GET':
        # If someone visits /upload in browser, show the upload page
        return render_template('upload.html')

    # POST: process the uploaded file
    if 'image' not in request.files:
        return "No file part"

    file = request.files['image']
    if file.filename == '':
        return "No selected file"

    data = file.read()

    # Generate random AES key
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    # Save encrypted file
    enc_filename = file.filename + '.enc'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
    with open(file_path, 'wb') as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

    # Convert key to hex and save it securely in keys.json
    key_hex = key.hex()
    save_key(enc_filename, key_hex)

    # Redirect to gallery page after successful upload
    flash("Image encrypted successfully!")
    return redirect(url_for('gallery'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
