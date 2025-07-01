import socket
import os
from tqdm import tqdm

PORT = 9999
BUFFER_SIZE = 4096

def start_receiver():
    os.makedirs("received_files", exist_ok=True)

    s = socket.socket()
    s.bind(("0.0.0.0", PORT))
    s.listen(1)
    print(f"[Receiver] Waiting for file on port {PORT}...")

    conn, addr = s.accept()
    print(f"[Receiver] Connected by {addr}")

    received = conn.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split("::")
    filename = os.path.basename(filename)
    filesize = int(filesize)

    filepath = os.path.join("received_files", filename)
    with open(filepath, "wb") as f:
        progress = tqdm(total=filesize, unit="B", unit_scale=True)
        while True:
            bytes_read = conn.recv(BUFFER_SIZE)
            if not bytes_read:
                break
            f.write(bytes_read)
            progress.update(len(bytes_read))
        progress.close()

    conn.close()
    print(f"[Receiver] File received: {filepath}")

if __name__ == "__main__":
    start_receiver()
