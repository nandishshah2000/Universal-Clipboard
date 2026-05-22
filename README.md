# 📋 Universal Clipboard

A lightweight, real-time web application that allows users to instantly share text and files across different networks and devices without the need for accounts or local network restrictions.

**🟢 Live Demo:** [Universal Clipboard](https://universal-clipboard-siic.onrender.com)
*(Note: Hosted on a free Render tier. If the app has been idle for 15 minutes, please allow ~50 seconds for the server to wake up on your first visit!)*

---

## ✨ Features
* **Real-Time Data Transfer:** Utilizes WebSockets for instant, low-latency text updates and file sharing between disparate networks (e.g., PC on Wi-Fi to Mobile on 5G).
* **Multi-Room Architecture:** Users generate unique, dynamic 4-digit room codes to create private, sandboxed sessions, supporting multiple concurrent users.
* **Automated Garbage Collection:** Engineered a background Python threading process that automatically shreds abandoned room data and local files after 1 hour of inactivity to optimize server memory.
* **Robust Security Boundaries:** Implemented strict application constraints, including:
  * 100MB maximum file upload limit.
  * Maximum capacity of 10 active rooms to prevent server bloat.
  * IP-based rate limiting (30 requests/minute) to mitigate DoS abuse.
* **Ephemeral Storage:** Server reboots automatically wipe the file system, ensuring no user data is permanently stored on the cloud host.
* **Progressive Web App (PWA):** Fully installable on iOS/Android home screens via custom Service Workers and Web Manifests for a native app experience.
* **Automated Testing:** Integrated Pytest suites to validate core server routing, error handling, and frontend rendering prior to deployment.

## 🛠️ Tech Stack
* **Backend:** Python 3, Flask
* **Real-Time Engine:** Flask-SocketIO, Gunicorn, Eventlet
* **Security:** Flask-Limiter, Python-dotenv
* **Frontend:** Vanilla HTML, CSS, JavaScript (Fetch API)
* **Deployment:** Render (CI/CD via GitHub)

---

## 🚀 Running Locally

If you would like to run this application on your local machine:

1. **Clone the repository:**
    git clone https://github.com/nandishshah2000/Universal-Clipboard.git
    cd Universal-Clipboard

2. **Install dependencies:**
    pip install -r requirements.txt

3. **Set your environment variables:**
    Create a .env file in the root directory and add:
    FLASK_SECRET_KEY=your_secure_random_key

4. **Start the application:**
    python app.py
    
    *(Note: The app will run on http://localhost:5000)*