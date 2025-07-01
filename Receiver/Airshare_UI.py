import sys
import os
import threading
import socket
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QStackedWidget, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPalette, QImage
from PyQt5.QtCore import Qt, QTimer
from gesture_detection import GestureDetector

# === SETTINGS ===
LAPTOP_A_IP = "# Replace with actual IP of Laptop A"  
COMMAND_PORT = 5055
TRANSFER_PORT = 9999
BUFFER_SIZE = 4096

# === Neon-style base widget ===
class NeonBase(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor("#0a0f1c"))
        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(0, 255, 255, 25))
        for x in range(0, self.width(), 40):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 40):
            painter.drawLine(0, y, self.width(), y)

class StartupPage(NeonBase):
    def __init__(self, switch_func):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png").scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("AIRSHARE")
        title.setFont(QFont("Orbitron", 36))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Share files with hand gestures")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #66ffff; font-size: 16px;")

        credits = QLabel("This project is made by Khogula Kannan")
        credits.setAlignment(Qt.AlignCenter)
        credits.setStyleSheet("color: #888888; font-size: 12px;")

        start_btn = QPushButton("🚀 Start Sharing")
        start_btn.setFixedWidth(220)
        start_btn.clicked.connect(switch_func)

        layout.addStretch()
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(subtitle)
        layout.addWidget(credits)
        layout.addSpacing(20)
        layout.addWidget(start_btn, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

class ModeSelectPage(NeonBase):
    def __init__(self, on_send, on_receive, on_back):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        label = QLabel("Choose Mode")
        label.setFont(QFont("Consolas", 22))
        label.setAlignment(Qt.AlignCenter)

        btn_send = QPushButton("📤 Send File")
        btn_receive = QPushButton("📥 Receive File")
        btn_back = QPushButton("🔙 Back")

        for btn in [btn_send, btn_receive, btn_back]:
            btn.setFixedWidth(200)

        btn_send.clicked.connect(self.show_disabled_notice)
        btn_receive.clicked.connect(on_receive)
        btn_back.clicked.connect(on_back)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(30)
        layout.addWidget(btn_send, alignment=Qt.AlignCenter)
        layout.addWidget(btn_receive, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_back, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

    def show_disabled_notice(self):
        QMessageBox.information(self, "Send Disabled", "Sending is only available on Laptop A.")

class ReceiverPage(NeonBase):
    def __init__(self, on_back):
        super().__init__()
        self.detector = GestureDetector()
        self.cap = None
        self.thrown = False
        self.backend_started = False

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        self.video_label = QLabel("Starting webcam...")
        self.video_label.setAlignment(Qt.AlignCenter)

        self.label = QLabel("🪃 Waiting for file throw...")
        self.label.setAlignment(Qt.AlignCenter)

        self.status = QLabel("Click Receive to begin.")
        self.status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setVisible(True)
        self.progress.setValue(0)

        back_btn = QPushButton("🔙 Back")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(on_back)

        layout.addWidget(self.video_label)
        layout.addSpacing(10)
        layout.addWidget(self.label)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addSpacing(10)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def start_backend_receiver(self):
        if self.backend_started:
            return
        self.backend_started = True

        self.cap = cv2.VideoCapture(0)

        def update():
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            frame, gesture = self.detector.detect(frame)

            if gesture == "throw" and not self.thrown:
                try:
                    self.status.setText("🪃 Throw detected. Requesting file...")
                    s = socket.socket()
                    s.connect((LAPTOP_A_IP, COMMAND_PORT))
                    s.sendall(b"SEND")
                    s.recv(1024)
                    self.thrown = True
                except Exception:
                    self.status.setText("❌ Failed to connect to sender.")

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(img).scaled(
                480, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.timer = QTimer(self)
        self.timer.timeout.connect(update)
        self.timer.start(30)

        threading.Thread(target=self.receive_file, daemon=True).start()

    def receive_file(self):
        os.makedirs("received_files", exist_ok=True)
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", TRANSFER_PORT))
        s.listen(1)

        conn, addr = s.accept()
        header = b""
        while b"<END>" not in header:
            header += conn.recv(1)

        header = header.decode().replace("<END>", "")
        filename, filesize_str = header.split("::")
        filesize = int(filesize_str)
        filepath = os.path.join("received_files", os.path.basename(filename))

        with open(filepath, "wb") as f:
            received = 0
            while received < filesize:
                data = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not data:
                    break
                f.write(data)
                received += len(data)
                self.progress.setValue(int(received * 100 / filesize))

        self.status.setText(f"✅ File received: {filename}")
        QTimer.singleShot(3000, QApplication.instance().quit)

class AirShareUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirShare")
        self.setFixedSize(900, 600)

        self.stack = QStackedWidget()
        self.startup = StartupPage(self.show_mode)
        self.mode = ModeSelectPage(self.fake_send, self.show_receiver, self.show_startup)
        self.receiver = ReceiverPage(self.show_mode)

        self.stack.addWidget(self.startup)
        self.stack.addWidget(self.mode)
        self.stack.addWidget(self.receiver)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def show_mode(self):
        self.stack.setCurrentWidget(self.mode)

    def show_receiver(self):
        self.stack.setCurrentWidget(self.receiver)
        self.receiver.start_backend_receiver()

    def show_startup(self):
        self.stack.setCurrentWidget(self.startup)

    def fake_send(self):
        pass  # Placeholder for send function on Laptop B

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
    window = AirShareUI()
    window.show()
    sys.exit(app.exec_())
