import socket
import os

TRANSFER_PORT = 9999
BUFFER_SIZE = 4096
RECEIVER_IP = "# Replace with your Laptop B IP address"  

# Optional progress callback for UI
progress_callback = None

def set_progress_callback(callback):
    global progress_callback
    progress_callback = callback

def send_file_to_receiver(filepath):
    print(f"[file_sender] ✅ send_file_to_receiver() called with: {filepath}")
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    
    try:
        with socket.socket() as s:
            s.connect((RECEIVER_IP, TRANSFER_PORT))

            # Step 1: Send header with delimiter
            header = f"{filename}::{filesize}<END>"
            s.sendall(header.encode())

            # Step 2: Send file content
            sent_bytes = 0
            with open(filepath, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    s.sendall(bytes_read)
                    sent_bytes += len(bytes_read)

                    # Update progress if callback is set
                    if progress_callback:
                        progress_percent = int((sent_bytes / filesize) * 100)
                        progress_callback(progress_percent)

        print("[Sender] ✅ File sent successfully!")

    except Exception as e:
        print(f"[Sender] ❌ Failed to send file: {e}")
