from flask import Flask, request, render_template
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        data = file.read()
        key = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename + '.enc')
        with open(file_path, 'wb') as f:
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)
        return f"Image uploaded and encrypted successfully! Key: {key.hex()}"
    return "No file uploaded"

if __name__ == '__main__':
    app.run(debug=True)
