import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QStackedWidget, QProgressBar
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPalette, QImage
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


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
        layout.setContentsMargins(0, 0, 0, 0)
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        label = QLabel("Choose Mode")
        label.setFont(QFont("Consolas", 22))
        label.setAlignment(Qt.AlignCenter)

        btn_send = QPushButton("📤 Send File")
        btn_receive = QPushButton("📥 Receive File")
        btn_back = QPushButton("🔙 Back")

        for btn in [btn_send, btn_receive, btn_back]:
            btn.setFixedWidth(200)

        btn_send.clicked.connect(on_send)
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


# ... [Imports and other classes remain the same above this] ...

class SenderPage(NeonBase):
    file_selected = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)

    def __init__(self, on_back):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        self.label = QLabel("📁 Select a file to transfer")
        self.label.setAlignment(Qt.AlignCenter)

        self.button = QPushButton("Choose File")
        self.button.setFixedWidth(200)
        self.button.clicked.connect(self.select_file)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setVisible(False)

        self.video_feed = QLabel()
        self.video_feed.setFixedHeight(240)
        self.video_feed.setStyleSheet("background-color: black;")
        self.video_feed.setVisible(False)

        back_btn = QPushButton("🔙 Back")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(on_back)

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addSpacing(10)
        layout.addWidget(self.video_feed, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)

        self.capture = None
        self.detector = None
        self.timer = QTimer()
        self.file_grabbed_flag = False
        self.filepath = None

        self.update_progress_signal.connect(self.update_progress)
        self.timer.timeout.connect(self.process_frame)

    def select_file(self):
        from file_selector import select_file
        file = select_file()
        if file:
            self.label.setText(f"File Selected:\n{file.split('/')[-1]}")
            self.status.setText("🪃 Waiting for grab gesture...")
            self.progress.setVisible(True)
            self.video_feed.setVisible(True)
            self.file_grabbed_flag = False
            self.filepath = file
            self.start_camera()
            self.file_selected.emit(file)

    def start_camera(self):
        from gesture_detection import GestureDetector
        self.capture = cv2.VideoCapture(0)
        self.detector = GestureDetector()
        self.timer.start(30)

    def process_frame(self):
        from file_storage import store_file
        if not self.capture or not self.capture.isOpened():
            return

        ret, frame = self.capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        frame, gesture = self.detector.detect(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_feed.setPixmap(QPixmap.fromImage(qt_img))

        if gesture == "grab" and not self.file_grabbed_flag:
            store_file(self.filepath)
            self.file_grabbed_flag = True
            self.status.setText("✅ Grab detected! File stored.")

    def update_progress(self, value):
        self.progress.setValue(value)
        if value >= 100:
            self.status.setText("✅ File sent successfully!")

    def closeEvent(self, event):
        self.timer.stop()
        if self.capture:
            self.capture.release()
        self.video_feed.clear()
        super().closeEvent(event)



class ReceiverPage(NeonBase):
    def __init__(self, on_back):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        self.label = QLabel("🪃 Waiting for file throw...")
        self.label.setAlignment(Qt.AlignCenter)

        self.status = QLabel("Listening for signal from Laptop A...")
        self.status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setVisible(True)

        back_btn = QPushButton("🔙 Back")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(on_back)

        layout.addStretch()
        layout.addWidget(self.label)
        layout.addSpacing(10)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addSpacing(10)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)

        self.simulate_receive()

    def simulate_receive(self):
        self.progress.setValue(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)

    def update_progress(self):
        value = self.progress.value()
        if value >= 100:
            self.timer.stop()
            self.status.setText("✅ File received successfully!")
        else:
            self.progress.setValue(value + 5)


class AirShareUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirShare")
        self.setFixedSize(900, 600)

        self.stack = QStackedWidget()
        self.startup = StartupPage(self.show_mode)
        self.mode = ModeSelectPage(self.show_sender, self.show_receiver, self.show_startup)
        self.sender = SenderPage(self.show_mode)
        self.receiver = ReceiverPage(self.show_mode)

        self.stack.addWidget(self.startup)
        self.stack.addWidget(self.mode)
        self.stack.addWidget(self.sender)
        self.stack.addWidget(self.receiver)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def show_mode(self):
        self.stack.setCurrentWidget(self.mode)

    def show_sender(self):
        self.stack.setCurrentWidget(self.sender)

    def show_receiver(self):
        self.stack.setCurrentWidget(self.receiver)

    def show_startup(self):
        self.stack.setCurrentWidget(self.startup)


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
