import sys
import threading
import socket
from PyQt5.QtWidgets import QApplication
from gesture_detection import GestureDetector  
from file_storage import store_file, get_stored_file
from file_sender import send_file_to_receiver, set_progress_callback
from Airshare_UI import AirShareUI 

PORT = 5055
HOST = "0.0.0.0"
file_grabbed_flag = False

# === TCP LISTENER ===
def start_listener():
    print(f"[Listener] Listening on {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)

    while True:
        conn, addr = s.accept()
        print(f"[Listener] Connection from {addr}")
        try:
            message = conn.recv(1024).decode().strip()
            print(f"[Listener] Received message: {message}")
            file = get_stored_file()
            if message == "SEND" and file:
                print(f"[Listener] Sending file: {file}")
                send_file_to_receiver(file)
                conn.sendall(b"SENT")
            else:
                conn.sendall(b"INVALID")
        except Exception as e:
            print(f"[Listener] Error: {e}")
        finally:
            conn.close()

# === USE Accurate Gesture Detection From gesture_detection.py ===
def start_gesture_loop(filepath):
    global file_grabbed_flag
    file_grabbed_flag = False  # Always reset

    def detect_loop():
        detector = GestureDetector()
        app_window.sender.detector = detector  # ✅ Assign detector to sender UI
        while not file_grabbed_flag:
            frame = app_window.sender.capture.read()[1] if app_window.sender.capture else None
            if frame is None:
                continue
            _, gesture = detector.detect(frame)
            if gesture == "grab":
                store_file(filepath)
                print("[Gesture] ✊ Grab detected — file stored.")
                app_window.sender.file_grabbed_flag = True
                break

    threading.Thread(target=detect_loop, daemon=True).start()

# === ENTRY POINT ===
if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QPushButton {
            background-color: rgba(0,255,255,0.05);
            border: 2px solid cyan;
            border-radius: 10px;
            padding: 10px;
            color: cyan;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: rgba(0,255,255,0.2);
        }
        QProgressBar {
            border: 2px solid cyan;
            border-radius: 5px;
            background-color: #111;
            height: 18px;
        }
        QProgressBar::chunk {
            background-color: cyan;
        }
        QLabel {
            color: cyan;
        }
    """)

    # 💠 Launch UI
    app_window = AirShareUI()
    app_window.show()

    # 💠 Start listener
    threading.Thread(target=start_listener, daemon=True).start()

    # 💠 Connect gesture loop to file selection
    app_window.sender.file_selected.connect(
        lambda filepath: start_gesture_loop(filepath)
    )

    # 💠 Connect backend progress updates to UI
    set_progress_callback(app_window.sender.update_progress)

    sys.exit(app.exec_())
