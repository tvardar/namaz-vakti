import os
import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QTextBrowser, QMessageBox,
                             QStyle, QApplication, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QDesktopServices, QCursor, QColor

from tasarim import LOGO_PATH


# --- GÜNCELLEME KONTROLÜ İÇİN İŞ PARÇACIĞI (THREAD) ---
class UpdateWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, user, repo):
        super().__init__()
        self.user = user
        self.repo = repo

    def run(self):
        result = {"status": "error", "data": None}
        try:
            url = f"https://api.github.com/repos/{self.user}/{self.repo}/releases/latest"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                result["status"] = "success"
                result["data"] = response.json()
            else:
                result["status"] = "not_found"
        except Exception:
            result["status"] = "connection_error"

        self.finished.emit(result)


# --- MODERN HAKKINDA DİYALOĞU ---
class HakkindaDialog(QDialog):
    def __init__(self, parent=None, version="v1.0", github_user="", repo_name="", web_url=""):
        super().__init__(parent)
        self.version = "v1.0"  # Sürüm sabitlendi
        self.github_user = github_user
        self.repo_name = repo_name
        self.github_repo_url = f"https://github.com/{github_user}/{repo_name}"
        self.web_url = web_url
        self.drag_pos = None

        # Pencere Ayarları
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 600)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Gölge için pay bırak

        # --- ARKA PLAN ÇERÇEVESİ ---
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1b26, stop:1 #24283b);
                border-radius: 20px; 
                border: 1px solid #414868; 
            }
        """)

        # Gölge Efekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.container.setGraphicsEffect(shadow)

        main_layout.addWidget(self.container)

        # İçerik Düzeni
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(25, 20, 25, 25)

        # --- 1. ÜST BAR (KAPAT BUTONU) ---
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        btn_close_x = QPushButton("✕")
        btn_close_x.setFixedSize(30, 30)
        btn_close_x.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close_x.setStyleSheet("""
            QPushButton { background: transparent; color: #565f89; border: none; font-size: 16px; font-weight: bold; }
            QPushButton:hover { color: #f7768e; background: rgba(247, 118, 142, 0.1); border-radius: 15px; }
        """)
        btn_close_x.clicked.connect(self.accept)
        top_bar.addWidget(btn_close_x)
        self.layout.addLayout(top_bar)

        # --- 2. LOGO VE BAŞLIK ---
        logo_area = QVBoxLayout()
        logo_area.setSpacing(5)

        # Logo
        logo_lbl = QLabel("🕌")
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            if not pix.isNull():
                logo_lbl.setPixmap(
                    pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                logo_lbl.setText("")

        logo_lbl.setStyleSheet("font-size: 60px; color: #7aa2f7; border: none;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_area.addWidget(logo_lbl)

        # Başlık
        title = QLabel(
            f"NAMAZ VAKTİ <span style='font-size:14px; color:#7dcfff; vertical-align:super;'>{self.version}</span>")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #c0caf5; border: none; margin-top: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_area.addWidget(title)

        # Geliştirici Bilgisi (Görünürlük Düzeltildi)
        author = QLabel("Geliştirici: <span style='color:#bb9af7; font-weight:bold;'>Tarık VARDAR</span>")
        author.setStyleSheet("color: #a9b1d6; font-size: 14px; margin-top: 2px; border: none;")
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author.setTextFormat(Qt.TextFormat.RichText)  # HTML desteği emin olmak için
        logo_area.addWidget(author)

        self.layout.addLayout(logo_area)
        self.layout.addSpacing(10)

        # --- 3. BAĞLANTI BUTONLARI ---
        btn_style = """
            QPushButton { 
                background-color: #24283b; color: #7aa2f7; 
                border: 1px solid #414868; padding: 10px; 
                border-radius: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { 
                background-color: #414868; color: white; border-color: #7aa2f7;
            }
        """

        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)

        btn_git = QPushButton(" GitHub Projesi")
        btn_git.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_git.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon))
        btn_git.setStyleSheet(btn_style)
        btn_git.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.github_repo_url)))

        btn_web = QPushButton(" Web Sitesi")
        btn_web.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_web.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        btn_web.setStyleSheet(btn_style)
        btn_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.web_url)))

        links_layout.addWidget(btn_git)
        links_layout.addWidget(btn_web)
        self.layout.addLayout(links_layout)

        # --- 4. GÜNCELLEME BUTONU ---
        self.btn_update = QPushButton("🔄 Güncellemeleri Kontrol Et")
        self.btn_update.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_update.setStyleSheet("""
            QPushButton { 
                background-color: rgba(16, 185, 129, 0.1); color: #10b981; 
                border: 1px dashed #10b981; padding: 12px; 
                border-radius: 8px; font-weight:bold; font-size: 13px;
            }
            QPushButton:hover { 
                background-color: #10b981; color: white; border-style: solid;
            }
        """)
        self.btn_update.clicked.connect(self.start_update_check)
        self.layout.addWidget(self.btn_update)

        # --- 5. YASAL UYARI VE LİSANS (Kutu İçinde) ---
        disclaimer_frame = QFrame()
        disclaimer_frame.setStyleSheet("background-color: #16161e; border-radius: 10px; border: 1px solid #24283b;")
        df_layout = QVBoxLayout(disclaimer_frame)
        df_layout.setContentsMargins(10, 10, 10, 10)

        disclaimer_box = QTextBrowser()
        disclaimer_box.setOpenExternalLinks(True)
        disclaimer_box.setFrameShape(QFrame.Shape.NoFrame)
        disclaimer_box.setStyleSheet("background: transparent; color: #a9b1d6; font-size: 11px; border: none;")

        disclaimer_text = (
            "<div style='font-family: sans-serif; text-align: center; line-height: 1.5;'>"
            "<p style='color:#bb9af7; font-weight:bold; margin-bottom:5px; font-size:12px;'>YASAL UYARI & LİSANS</p>"
            "<p>Bu yazılım <b>MIT Lisansı</b> ile tamamen ücretsiz ve açık kaynak kodlu olarak dağıtılmaktadır.</p>"
            "<p>Uygulamada gösterilen vakit verileri, çevrimiçi açık kaynak API servisleri aracılığıyla anlık olarak temin edilmektedir. "
            "Coğrafi konum hassasiyetine veya internet bağlantısına bağlı olarak 1-2 dakikalık sapmalar oluşabilir. "
            "Lütfen ibadet vakitlerinde temkinli olunuz.</p>"
            "<p style='color:#565f89; font-style:italic;'>Bu proje kâr amacı gütmeyen, gönüllü bir çalışmadır.</p>"
            "</div>"
        )
        disclaimer_box.setHtml(disclaimer_text)
        disclaimer_box.setFixedHeight(140)  # Sabit yükseklik

        df_layout.addWidget(disclaimer_box)
        self.layout.addWidget(disclaimer_frame)

        self.layout.addStretch()

        # --- 6. ALT KAPAT BUTONU ---
        btn_close_bottom = QPushButton("Kapat")
        btn_close_bottom.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close_bottom.setStyleSheet("""
            QPushButton { 
                background-color: #f7768e; color: white; 
                padding: 12px; border-radius: 8px; 
                font-weight: 900; border:none; letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #ff9eaf; }
        """)
        btn_close_bottom.clicked.connect(self.accept)
        self.layout.addWidget(btn_close_bottom)

    # --- SÜRÜKLE BIRAK MANTIĞI ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            new_pos = event.globalPosition().toPoint()
            diff = new_pos - self.drag_pos
            self.move(self.pos() + diff)
            self.drag_pos = new_pos

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    # --- GÜNCELLEME KONTROLÜ ---
    def start_update_check(self):
        self.btn_update.setText("⏳ Kontrol ediliyor...")
        self.btn_update.setEnabled(False)

        # Thread başlat
        self.worker = UpdateWorker(self.github_user, self.repo_name)
        self.worker.finished.connect(self.handle_update_result)
        self.worker.start()

    def handle_update_result(self, result):
        self.btn_update.setEnabled(True)
        status = result["status"]

        if status == "success":
            data = result["data"]
            latest_version = data.get("tag_name", "")

            if latest_version != self.version and latest_version:
                self.btn_update.setText("Yeni Sürüm Mevcut! 🎉")
                self.btn_update.setStyleSheet(
                    "background-color: #e0af68; color: #1a1b26; border: none; font-weight: bold; padding: 12px; border-radius: 8px;")

                msg = QMessageBox(self)
                msg.setWindowTitle("Güncelleme")
                msg.setText(f"Yeni Sürüm Bulundu: {latest_version}")
                msg.setInformativeText("İndirme sayfasına gitmek ister misiniz?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg.setStyleSheet("background-color: #1a1b26; color: white;")
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(QUrl(data.get("html_url")))
            else:
                self.btn_update.setText("Sürümünüz Güncel ✔")
                self.btn_update.setStyleSheet(
                    "background-color: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; padding: 12px; border-radius: 8px; font-weight:bold;")
                QTimer.singleShot(3000, self.reset_update_btn)

        elif status == "connection_error":
            self.btn_update.setText("Bağlantı Hatası ❌")
            QTimer.singleShot(3000, self.reset_update_btn)

        else:
            self.btn_update.setText("Bilgi Alınamadı ❓")
            QTimer.singleShot(3000, self.reset_update_btn)

    def reset_update_btn(self):
        self.btn_update.setText("🔄 Güncellemeleri Kontrol Et")
        self.btn_update.setStyleSheet("""
            QPushButton { 
                background-color: rgba(16, 185, 129, 0.1); color: #10b981; 
                border: 1px dashed #10b981; padding: 12px; 
                border-radius: 8px; font-weight:bold; 
            }
            QPushButton:hover { 
                background-color: #10b981; color: white; border-style: solid;
            }
        """)