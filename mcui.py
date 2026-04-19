import sys
import os
import time
import re
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QTextEdit, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

class LogMonitorThread(QThread):
    new_message = pyqtSignal(str)
    error_message = pyqtSignal(str)

    def __init__(self, log_path, use_filter, filter_list, use_blacklist, blacklist):
        super().__init__()
        self.log_path = log_path
        self.use_filter = use_filter
        self.filter_list = filter_list
        self.use_blacklist = use_blacklist
        self.blacklist = blacklist
        self.is_running = True

    def run(self):
        self.new_message.emit("Program started")
        try:
            with open(self.log_path, 'r', encoding="utf-8", errors="ignore") as file:
                file.seek(0, os.SEEK_END)
                while self.is_running:
                    line = file.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    self.process_chat_message(line)
        except FileNotFoundError:
            self.error_message.emit(f"Error! Could not open the log file on the following path: {self.log_path}")
        except Exception as e:
            self.error_message.emit(f"An error occurred: {str(e)}")

    def process_chat_message(self, msg):
        msg = re.sub(r'[\uE000-\uF8FF\u3000-\u9FFF\uFFFD]', '', msg)
        
        msg_lower = msg.lower()
        if "[chat]" not in msg_lower:
            return
        
        if self.use_blacklist:
            if any(b.lower() in msg_lower for b in self.blacklist):
                return
                
        if self.use_filter:
            if not any(f.lower() in msg_lower for f in self.filter_list):
                return
                
        msg_split = msg.strip().split(" ")
        
        for x in range(4):
            if len(msg_split) > 1:
                msg_split.pop(1)
                
        if len(msg_split) > 1 and msg_split[1] and all(char == '?' for char in msg_split[1]):
            msg_split.pop(1)
            
        self.new_message.emit(" ".join(msg_split).replace("  ", " ").strip())

    def stop(self):
        self.is_running = False
        self.new_message.emit("Program stopped")

class LogApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Minecraft log monitor")
        self.resize(900, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { color: #d4d4d4; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #3c3c3c; padding: 6px; border-radius: 4px; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:disabled { background-color: #333333; color: #777777; }
            QTextEdit { background-color: #1e1e1e; border: 1px solid #3c3c3c; padding: 8px; font-family: 'Consolas', monospace; border-radius: 4px; }
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #3c3c3c; border-radius: 3px; background-color: #2d2d2d; }
            QCheckBox::indicator:checked { background-color: #0e639c; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        
        default_log_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "logs", "latest.log").replace("\\", "/")
        self.file_input.setText(default_log_path)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(QLabel("Log path:"))
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_btn)
        main_layout.addLayout(file_layout)

        filter_layout = QHBoxLayout()
        self.use_filter_cb = QCheckBox("Use filter")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Allowed words (e.g. gold, golden)")
        self.use_blacklist_cb = QCheckBox("Use blacklist")
        self.use_blacklist_cb.setChecked(True)
        self.blacklist_input = QLineEdit()
        self.blacklist_input.setPlaceholderText("Blocked words (e.g. ad, webshop)")
        
        filter_layout.addWidget(self.use_filter_cb)
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(self.use_blacklist_cb)
        filter_layout.addWidget(self.blacklist_input)
        main_layout.addLayout(filter_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search console...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_console)
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.search_btn)
        main_layout.addLayout(control_layout)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        main_layout.addWidget(self.console)

        self.monitor_thread = None

        self.use_filter_cb.toggled.connect(self.update_filters)
        self.filter_input.textChanged.connect(self.update_filters)
        self.use_blacklist_cb.toggled.connect(self.update_filters)
        self.blacklist_input.textChanged.connect(self.update_filters)

    def update_filters(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.use_filter = self.use_filter_cb.isChecked()
            self.monitor_thread.filter_list = [f.strip() for f in self.filter_input.text().split(",") if f.strip()]
            self.monitor_thread.use_blacklist = self.use_blacklist_cb.isChecked()
            self.monitor_thread.blacklist = [b.strip() for b in self.blacklist_input.text().split(",") if b.strip()]

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select log file", "", "Log Files (*.log);;All Files (*)")
        if file_path:
            self.file_input.setText(file_path)

    def append_console(self, text):
        self.console.append(text)

    def display_error(self, text):
        self.console.append(text)
        self.stop_monitoring()

    def start_monitoring(self):
        log_path = self.file_input.text()
        if not log_path or not os.path.exists(log_path):
            QMessageBox.warning(self, "Error", "Please select a valid log file path!")
            return

        use_filter = self.use_filter_cb.isChecked()
        filter_list = [f.strip() for f in self.filter_input.text().split(",") if f.strip()]
        use_blacklist = self.use_blacklist_cb.isChecked()
        blacklist = [b.strip() for b in self.blacklist_input.text().split(",") if b.strip()]

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.monitor_thread = LogMonitorThread(log_path, use_filter, filter_list, use_blacklist, blacklist)
        self.monitor_thread.new_message.connect(self.append_console)
        self.monitor_thread.error_message.connect(self.display_error)
        self.monitor_thread.start()

    def stop_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def search_console(self):
        search_text = self.search_input.text()
        
        cursor = self.console.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        format_clear = QTextCharFormat()
        format_clear.setBackground(QColor("#1e1e1e"))
        format_clear.setForeground(QColor("#d4d4d4"))
        cursor.mergeCharFormat(format_clear)
        
        if not search_text:
            return
            
        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QColor("#f73030"))
        format_highlight.setForeground(QColor("#000000"))
        
        self.console.moveCursor(QTextCursor.MoveOperation.Start)
        while self.console.find(search_text):
            cursor = self.console.textCursor()
            cursor.mergeCharFormat(format_highlight)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LogApp()
    window.show()
    sys.exit(app.exec())