import cv2
import threading
import socket
from gesture_detection import GestureDetector
from file_selector import select_file
from file_storage import store_file, get_stored_file
from file_sender import send_file_to_receiver

# === GLOBALS ===
PORT = 5055
HOST = "0.0.0.0"

# === Gesture Setup ===
detector = GestureDetector()
cap = cv2.VideoCapture(0)
file_grabbed = False

# === Function: Listener Thread ===
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
                send_file_to_receiver(file)  # ✅ FIXED: pass the filepath here
                conn.sendall(b"SENT")
            else:
                conn.sendall(b"INVALID")
        except Exception as e:
            print(f"[Listener] Error: {e}")
        finally:
            conn.close()

# === Start Listener in Background ===
listener_thread = threading.Thread(target=start_listener, daemon=True)
listener_thread.start()

# === File Selection ===
selected_file = select_file()

# === Main Camera Loop ===
while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame, gesture = detector.detect(frame)

    if gesture == "grab" and selected_file and not file_grabbed:
        store_file(selected_file)
        file_grabbed = True
        print("[Sender] File grabbed and ready to send when Laptop B throws.")

    cv2.imshow("Laptop A - AirShare Sender", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
