import cv2
import threading
import socket
import os
from tqdm import tqdm
from gesture_detection import GestureDetector

# === SETTINGS ===
LAPTOP_A_IP = "# Replace with actual IP of Laptop A"  # <-- Replace with actual Laptop A IP
COMMAND_PORT = 5055
TRANSFER_PORT = 9999
BUFFER_SIZE = 4096

# === Gesture Detector Setup ===
detector = GestureDetector()
cap = cv2.VideoCapture(0)
thrown = False  # Flag to avoid sending multiple SEND signals

# === File Receiving Thread ===
def receive_file():
    import socket
    import os
    from tqdm import tqdm

    TRANSFER_PORT = 9999
    BUFFER_SIZE = 4096

    os.makedirs("received_files", exist_ok=True)

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", TRANSFER_PORT))
    s.listen(1)
    print(f"[Receiver] Waiting for file on port {TRANSFER_PORT}...")

    conn, addr = s.accept()
    print(f"[Receiver] Connected by {addr}")

    try:
        # Step 1: Receive header until <END>
        header = b""
        while b"<END>" not in header:
            chunk = conn.recv(1)
            if not chunk:
                raise Exception("Connection closed before receiving header.")
            header += chunk

        header = header.decode().replace("<END>", "")
        filename, filesize_str = header.split("::")
        if not filesize_str.isdigit():
            raise Exception("Received invalid file size.")

        filesize = int(filesize_str)
        filename = os.path.basename(filename)
        filepath = os.path.join("received_files", filename)

        print(f"[Receiver] Receiving: {filename} ({filesize} bytes)")

        # Step 2: Receive file
        with open(filepath, "wb") as f:
            total_received = 0
            progress = tqdm(total=filesize, unit="B", unit_scale=True)

            while total_received < filesize:
                bytes_read = conn.recv(min(BUFFER_SIZE, filesize - total_received))
                if not bytes_read:
                    break
                f.write(bytes_read)
                total_received += len(bytes_read)
                progress.update(len(bytes_read))
            progress.close()

        print(f"[Receiver] ✅ File received successfully: {filepath}")

    except Exception as e:
        print(f"[Receiver] ❌ Error while receiving file: {e}")
    finally:
        conn.close()




# === Start Receiver in Background ===
receiver_thread = threading.Thread(target=receive_file, daemon=True)
receiver_thread.start()

# === Main Webcam Loop for Throw Gesture ===
while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame, gesture = detector.detect(frame)

    if gesture == "throw" and not thrown:
        print("[Receiver] 🪃 Throw detected. Sending 'SEND' signal to Laptop A...")
        try:
            s = socket.socket()
            s.connect((LAPTOP_A_IP, COMMAND_PORT))
            s.sendall(b"SEND")
            response = s.recv(1024).decode()
            print(f"[Receiver] Response from A: {response}")
            thrown = True
        except Exception as e:
            print("[Receiver] ❌ ERROR sending signal to A:", e)

    cv2.imshow("Laptop B - AirShare Receiver", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
