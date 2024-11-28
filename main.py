import sys
import yt_dlp as youtube_dl
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import re
import json
import os

class MyLogger(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def debug(self, msg):
        self.log_signal.emit(msg)

    def warning(self, msg):
        self.log_signal.emit(f'WARNING: {msg}')

    def error(self, msg):
        self.log_signal.emit(f'ERROR: {msg}')

def remove_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

class DownloadThread(QThread):
    progress_signal = pyqtSignal(float)
    finished_signal = pyqtSignal()
    log_signal = pyqtSignal(str)
    higher_quality_signal = pyqtSignal(bool)

    def __init__(self, video_url, download_path, quality, file_format):
        super().__init__()
        self.video_url = video_url
        self.download_path = download_path
        self.quality = quality
        self.file_format = file_format

    def run(self):
        logger = MyLogger()
        logger.log_signal.connect(self.log_signal)
        ydl_opts = {
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'format': f'bestvideo[height<={self.quality}]+bestaudio/best' if self.file_format in ['mp4', 'webm'] else 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.file_format,
            }] if self.file_format in ['mp4', 'webm'] else [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'logger': logger,
            'progress_hooks': [self.progress_hook]
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.video_url, download=False)
                formats = info_dict.get('formats', [])
                higher_quality_available = any(f.get('height') and int(f['height']) > int(self.quality) for f in formats)
                self.higher_quality_signal.emit(higher_quality_available)
                ydl.download([self.video_url])
            self.finished_signal.emit()
        except Exception as e:
            self.log_signal.emit(f'下載失敗：{e}')
            self.finished_signal.emit()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = remove_ansi_escape_sequences(d['_percent_str'])
            self.progress_signal.emit(float(p.strip('%')))
        elif d['status'] == 'finished':
            self.progress_signal.emit(100)

class CheckResolutionsThread(QThread):
    resolutions_signal = pyqtSignal(list)
    log_signal = pyqtSignal(str)

    def __init__(self, video_url):
        super().__init__()
        self.video_url = video_url

    def run(self):
        logger = MyLogger()
        logger.log_signal.connect(self.log_signal)
        ydl_opts = {
            'logger': logger,
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.video_url, download=False)
                formats = info_dict.get('formats', [])
                resolutions = sorted(set(f.get('height') for f in formats if f.get('height')))
                self.resolutions_signal.emit(resolutions)
        except Exception as e:
            self.log_signal.emit(f'檢測失敗：{e}')

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.load_translations()
        self.initUI()

    def load_translations(self):
        translations_path = os.path.join(os.path.dirname(__file__), 'translations.json')
        if not os.path.exists(translations_path):
            QMessageBox.critical(self, "Error", f"Translations file not found: {translations_path}")
            sys.exit(1)
        with open(translations_path, 'r', encoding='utf-8') as f:
            self.translations = json.load(f)

    def initUI(self):
        self.setWindowTitle(self.translations["繁體中文"]["window_title"])
        self.setGeometry(100, 100, 850, 600)

        self.dark_style = """
            QWidget {
                background-color: black;
                color: #00FF00;
                font-size: 25px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #333;
                color: #00FF00;
                border: 2px solid #00FF00;
                border-radius: 10px;
                padding: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QLineEdit:hover {
                background-color: #555;
            }
            QPushButton {
                background-color: #333;
                color: #00FF00;
                border: 2px solid #00FF00;
                border-radius: 10px;
                padding: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QPushButton:hover {
                background-color: #555;
            }
            QProgressBar {
                background-color: #333;
                color: #00FF00;
                border: 2px solid #00FF00;
                border-radius: 10px;
                text-align: center;
                height: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QProgressBar::chunk {
                background-color: #00FF00;
            }
        """

        self.light_style = """
            QWidget {
                background-color: white;
                color: black;
                font-size: 25px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #f0f0f0;
                color: black;
                border: 2px solid black;
                border-radius: 10px;
                padding: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QLineEdit:hover {
                background-color: #e0e0e0;
            }
            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 2px solid black;
                border-radius: 10px;
                padding: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QProgressBar {
                background-color: #f0f0f0;
                color: black;
                border: 2px solid black;
                border-radius: 10px;
                text-align: center;
                height: 5px;
                font-family: 'Microsoft JhengHei', 'Cascadia Mono';
            }
            QProgressBar::chunk {
                background-color: black;
            }
        """

        self.setStyleSheet(self.dark_style)

        layout = QVBoxLayout()

        # 視窗風格和語言選擇
        settings_layout = QHBoxLayout()
        self.style_label = QLabel(self.translations["繁體中文"]["select_style"])
        self.style_combobox = QComboBox()
        self.style_combobox.addItems([self.translations["繁體中文"]["dark"], self.translations["繁體中文"]["light"]])
        self.style_combobox.currentIndexChanged.connect(self.change_style)
        self.language_label = QLabel(self.translations["繁體中文"]["select_language"])
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(["繁體中文", "English", "簡體中文", "日本語"])
        self.language_combobox.currentIndexChanged.connect(self.change_language)
        settings_layout.addWidget(self.style_label)
        settings_layout.addWidget(self.style_combobox)
        settings_layout.addWidget(self.language_label)
        settings_layout.addWidget(self.language_combobox)
        layout.addLayout(settings_layout)

        # 影片網址輸入和檢測按鈕
        url_layout = QHBoxLayout()
        self.url_label = QLabel(self.translations["繁體中文"]["youtube_url"])
        self.url_entry = QLineEdit()
        self.check_button = QPushButton(self.translations["繁體中文"]["check_resolutions"])
        self.check_button.clicked.connect(self.check_resolutions)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_entry)
        url_layout.addWidget(self.check_button)
        layout.addLayout(url_layout)

        # 下載路徑選擇
        path_layout = QHBoxLayout()
        self.path_label = QLabel(self.translations["繁體中文"]["download_path"])
        self.path_entry = QLineEdit()
        self.path_button = QPushButton(self.translations["繁體中文"]["select_path"])
        self.path_button.clicked.connect(self.select_path)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_entry)
        path_layout.addWidget(self.path_button)
        layout.addLayout(path_layout)

        # 畫質和格式選擇
        options_layout = QHBoxLayout()
        self.quality_label = QLabel(self.translations["繁體中文"]["select_quality"])
        self.quality_combobox = QComboBox()
        self.quality_combobox.addItems(["1080", "720", "480", "360"])
        self.format_label = QLabel(self.translations["繁體中文"]["select_format"])
        self.format_combobox = QComboBox()
        self.format_combobox.addItems(["webm", "mp4", "mp3"])
        options_layout.addWidget(self.quality_label)
        options_layout.addWidget(self.quality_combobox)
        options_layout.addWidget(self.format_label)
        options_layout.addWidget(self.format_combobox)
        layout.addLayout(options_layout)

        # 下載按鈕
        self.download_button = QPushButton(self.translations["繁體中文"]["download"])
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # 日誌顯示
        self.log_label = QLabel(self.translations["繁體中文"]["log"])
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def change_style(self):
        if self.style_combobox.currentText() == self.translations[self.language_combobox.currentText()]["dark"]:
            self.setStyleSheet(self.dark_style)
        else:
            self.setStyleSheet(self.light_style)

    def change_language(self):
        lang = self.language_combobox.currentText()
        self.setWindowTitle(self.translations[lang]["window_title"])
        self.style_label.setText(self.translations[lang]["select_style"])
        self.language_label.setText(self.translations[lang]["select_language"])
        self.style_combobox.setItemText(0, self.translations[lang]["dark"])
        self.style_combobox.setItemText(1, self.translations[lang]["light"])
        self.url_label.setText(self.translations[lang]["youtube_url"])
        self.check_button.setText(self.translations[lang]["check_resolutions"])
        self.path_label.setText(self.translations[lang]["download_path"])
        self.path_button.setText(self.translations[lang]["select_path"])
        self.quality_label.setText(self.translations[lang]["select_quality"])
        self.format_label.setText(self.translations[lang]["select_format"])
        self.download_button.setText(self.translations[lang]["download"])
        self.log_label.setText(self.translations[lang]["log"])

    def select_path(self):
        lang = self.language_combobox.currentText()
        path = QFileDialog.getExistingDirectory(self, self.translations[lang]["select_download_path"])
        if path:
            self.path_entry.setText(path)

    def check_resolutions(self):
        lang = self.language_combobox.currentText()
        url = self.url_entry.text()
        if not url:
            QMessageBox.warning(self, self.translations[lang]["warning"], self.translations[lang]["enter_url"])
            return

        self.check_thread = CheckResolutionsThread(url)
        self.check_thread.resolutions_signal.connect(self.update_resolutions)
        self.check_thread.log_signal.connect(self.update_log)
        self.check_thread.start()

    def update_resolutions(self, resolutions):
        self.quality_combobox.clear()
        self.quality_combobox.addItems(map(str, resolutions))

    def start_download(self):
        lang = self.language_combobox.currentText()
        url = self.url_entry.text()
        path = self.path_entry.text()
        quality = self.quality_combobox.currentText()
        file_format = self.format_combobox.currentText()
        if not url:
            QMessageBox.warning(self, self.translations[lang]["warning"], self.translations[lang]["enter_url"])
            return
        if not path:
            QMessageBox.warning(self, self.translations[lang]["warning"], self.translations[lang]["select_download_path"])
            return

        # 重置進度條和日誌顯示區域
        self.progress_bar.setValue(0)
        self.log_text.clear()

        self.download_thread = DownloadThread(url, path, quality, file_format)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.log_signal.connect(self.update_log)
        self.download_thread.higher_quality_signal.connect(self.notify_higher_quality)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def update_log(self, message):
        self.log_text.append(message)

    def notify_higher_quality(self, available):
        lang = self.language_combobox.currentText()
        if available:
            QMessageBox.information(self, self.translations[lang]["notice"], self.translations[lang]["higher_quality_available"])

    def download_finished(self):
        lang = self.language_combobox.currentText()
        QMessageBox.information(self, self.translations[lang]["success"], self.translations[lang]["download_completed"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec_())