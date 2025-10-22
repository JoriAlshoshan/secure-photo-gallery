import os
from flask import Flask, request, render_template, redirect, url_for , flash, session
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your secret_key'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/gallery')
def gallery():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if not f.startswith('.')]
    return render_template('gallery.html', uploaded_files=files , logo_image='logo.png')


@app.route('/upload', methods=['POST'])
def upload():
    
    if 'image' not in request.files:
        return "No file part"
    
    file = request.files['image']
    if file.filename == '':
        return "No selected file"
    
    if file:
        data = file.read()
        key = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        enc_filename = file.filename + '.enc'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
        with open(file_path, 'wb') as f:
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)
            
        key_hex = key.hex() 
        flash(f"Image encrypted successfully! Key: {key_hex}")
        return redirect(url_for('gallery'))
    
    
if __name__ == '__main__':
    app.run(debug=True ,port=5001)
