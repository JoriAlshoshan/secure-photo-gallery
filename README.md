# Secure Photo Gallery

**Secure Photo Gallery** is a **web-based application** developed using **Python and Flask** to provide a secure way to upload, store, and manage personal photos. The project focuses on **data privacy** by encrypting photos with **AES encryption** before storing them, ensuring that only authorized users can access the original images.  

---

## Project Idea / Concept

The goal of this project is to create a **secure photo gallery** where users can:

- Upload images safely through a web interface  
- Automatically encrypt uploaded images using AES  
- Store photos securely on the server  
- Retrieve and decrypt images only with the correct encryption key  

This ensures **confidentiality, integrity, and privacy** of users’ photos, making it suitable for personal or sensitive data storage.

---

## Team Members and Roles

### **Student 1 – Jori Alshoshan**
- **Role:** Project Setup + Encryption  
- **Tasks:** Set up Flask project (`app.py`), create basic photo upload page, implement AES encryption.   

### **Student 2 – Fatimah Alkhuraiji**
- **Role:** Login + Database  
- **Tasks:** Implement Register/Login system, SQLite database.   

### **Student 3 – Norah Alyahq**
- **Role:** Front-End / User Interface  
- **Tasks:** Enhance pages with HTML/CSS/Bootstrap, design photo gallery.    

### **Student 4 – Rafah Aljabri**
- **Role:** Download + Decryption + Testing  
- **Tasks:** Implement photo download and decryption, test the system.  

---

## Key Features

1. **User Interface** – Simple and responsive web pages for uploading and viewing photos.  
2. **Photo Upload** – Supports common image formats (JPEG, PNG, etc.).  
3. **AES Encryption** – Each uploaded image is encrypted with a randomly generated AES key.  
4. **Secure Storage** – Encrypted images are stored safely on the server.  
5. **Retrieval & Decryption** – Only authorized users can decrypt and view the original image.  

---

## Project Goal

This project is designed to **practice implementing AES cryptography** in a real-world scenario while ensuring **usability and privacy**. Users can securely manage their photos without risk of unauthorized access.  

---

## Technologies Used

- Python 3.x  
- Flask (Web framework)  
- PyCryptodome (AES encryption)  
- HTML/CSS (Front-end templates)  
- SQLite (Database)  
- Git / GitHub (Version control)  

---

## How to Run the Project

1. Clone the repository:  
```
git clone <repository-url
```
2. Navigate to the project folder:
```
cd secure_photo_gallery
```
3. Create and activate a virtual environment:
 ```
 python -m venv venv
 venv\Scripts\activate
 ```
4. Install required packages:
 ```
 pip install -r requirements.txt
 ```
5. Run the application:
 ```
 python app.py
 ```
6. Open a web browser and go to:
 ```
 http://127.0.0.1:5000/
 ```
## Contact

Jori Alshoshan – jori.alshoshan@gmail.com

Fatimah Alkhuraiji –

Norah Alyahq – 

Rafah Aljabri –

© 2025 Secure Photo Gallery



