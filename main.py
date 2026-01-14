import sys
import datetime
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QSystemTrayIcon, QMenu,
                             QFrame, QCalendarWidget, QDialog, QToolTip)
from PyQt6.QtCore import Qt, QTimer, QSettings, QDate, QPoint, QLockFile, QDir
from PyQt6.QtGui import QIcon, QAction, QTextCharFormat, QColor, QFont, QBrush

# Kendi modüllerimiz
from tasarim import LocationDialog, AyarlarDialog, LOGO_PATH
from hakkinda import HakkindaDialog
from backend import NamazBackend

# =============================================================================
# NAMAZ VAKTİ HUD v1.0
# =============================================================================

VERSION = "v1.0"
GITHUB_USER = "tvardar"
REPO_NAME = "namaz-vakti"
WEBSITE_URL = "https://tarikvardar.com.tr"

# --- GUNLER.XLSX VERİLERİ (2026 - KESİN LİSTE) ---

NATIONAL_HOLIDAYS = {
    (1, 1): "Yılbaşı",
    (3, 18): "18 Mart Çanakkale Zaferi",
    (4, 23): "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı",
    (5, 1): "1 Mayıs Emek ve Dayanışma Günü",
    (5, 19): "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı",
    (7, 15): "15 Temmuz Demokrasi ve Milli Birlik Günü",
    (8, 30): "30 Ağustos Zafer Bayramı",
    (10, 29): "29 Ekim Cumhuriyet Bayramı",
    (11, 10): "10 Kasım Atatürk'ü Anma Günü"
}

RELIGIOUS_HOLIDAYS_2026 = {
    (1, 15): "Miraç Kandili",
    (2, 2): "Berat Kandili",
    (2, 19): "Ramazan Başlangıcı",
    (3, 16): "Kadir Gecesi",
    (3, 19): "Arefe (Ramazan)",
    (3, 20): "Ramazan Bayramı 1. Gün",
    (3, 21): "Ramazan Bayramı 2. Gün",
    (3, 22): "Ramazan Bayramı 3. Gün",
    (5, 26): "Arefe (Kurban)",
    (5, 27): "Kurban Bayramı 1. Gün",
    (5, 28): "Kurban Bayramı 2. Gün",
    (5, 29): "Kurban Bayramı 3. Gün",
    (5, 30): "Kurban Bayramı 4. Gün",
    (6, 16): "Hicri Yılbaşı (1 Muharrem)",
    (6, 25): "Aşure Günü",
    (8, 24): "Mevlid Kandili",
    (12, 10): "Regaib Kandili"
}


# --- GELİŞMİŞ TAKVİM WIDGET'I ---
class HolidayCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QCalendarWidget QWidget { 
                background-color: #1a1b26; 
                alternate-background-color: #24283b; 
                color: #c0caf5; 
            }
            QCalendarWidget QToolButton { 
                color: #7aa2f7; icon-size: 24px; font-weight: bold; background: transparent;
                border-radius: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: rgba(255,255,255,0.1);
            }
            QCalendarWidget QMenu { 
                background-color: #1a1b26; color: white; border: 1px solid #414868;
            }
            QCalendarWidget QSpinBox { 
                background-color: #24283b; color: white; selection-background-color: #7aa2f7; border-radius: 4px;
            }
            QCalendarWidget QAbstractItemView:enabled { 
                color: #c0caf5; 
                selection-background-color: #7aa2f7; 
                selection-color: white; 
                font-size: 14px;
                outline: 0;
            }
            QCalendarWidget QAbstractItemView:disabled { color: #565f89; }
        """)
        self.highlight_holidays()

    def highlight_holidays(self):
        fmt_national = QTextCharFormat()
        fmt_national.setForeground(QColor("#ff5555"))
        fmt_national.setFontWeight(QFont.Weight.Bold)
        fmt_national.setBackground(QBrush(QColor(255, 85, 85, 30)))

        fmt_religious = QTextCharFormat()
        fmt_religious.setForeground(QColor("#50fa7b"))
        fmt_religious.setFontWeight(QFont.Weight.Bold)
        fmt_religious.setBackground(QBrush(QColor(80, 250, 123, 30)))

        current_year = QDate.currentDate().year()

        for year in range(current_year - 1, current_year + 2):
            for (month, day) in NATIONAL_HOLIDAYS:
                try:
                    date = QDate(year, month, day)
                    self.setDateTextFormat(date, fmt_national)
                except:
                    pass

        for (month, day) in RELIGIOUS_HOLIDAYS_2026:
            try:
                date = QDate(2026, month, day)
                self.setDateTextFormat(date, fmt_religious)
            except:
                pass

    def mouseMoveEvent(self, event):
        try:
            pos = event.position().toPoint()
            date = self.dateAt(pos)
            if date.isValid():
                key_nat = (date.month(), date.day())
                key_rel = (date.month(), date.day())
                tooltip_text = ""

                if key_nat in NATIONAL_HOLIDAYS:
                    tooltip_text = NATIONAL_HOLIDAYS[key_nat]
                elif date.year() == 2026 and key_rel in RELIGIOUS_HOLIDAYS_2026:
                    tooltip_text = RELIGIOUS_HOLIDAYS_2026[key_rel]

                if tooltip_text:
                    QToolTip.setFont(QFont("Segoe UI", 10))
                    self.setToolTip(tooltip_text)
                else:
                    self.setToolTip("")
            else:
                self.setToolTip("")
        except:
            pass
        super().mouseMoveEvent(event)


class CalendarDialog(QDialog):
    def __init__(self, parent=None, current_date=None):
        super().__init__(parent)
        self.setWindowTitle("Tarih Seç")
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFixedSize(400, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.calendar = HolidayCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        if current_date:
            self.calendar.setSelectedDate(current_date)

        self.calendar.clicked.connect(self.accept)
        layout.addWidget(self.calendar)

    def get_date(self):
        return self.calendar.selectedDate()


class NamazHUD(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("NamazVakti", "Settings")
        self.view_date = QDate.currentDate()
        self.m_pos = None # X11 taşıma için

        # Backend
        self.backend = NamazBackend()

        self.load_app_settings()

        self.vakitler = []
        self.hijri_date = None
        self.current_city = "Yükleniyor..."
        self.is_ramadan = False
        self.ramadan_times = {}

        self.app_icon = QIcon(LOGO_PATH)
        self.setWindowIcon(self.app_icon)

        self.init_ui()
        self.backend.stop_btn_ref = self.btn_stop_sound

        self.init_tray()
        
        # İlk açılışta konum kontrolü
        if not self.settings.value("district_id"):
            QTimer.singleShot(500, self.open_location_dialog)
        else:
            self.fetch_data()
            
        self.create_autostart_entry()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(1000)

    def load_app_settings(self):
        self.uyari_dk = self.settings.value("warning_min", 15, type=int)
        self.ses_aktif = self.settings.value("audio_enabled", True, type=bool)
        self.vakit_girdi_tipi = self.settings.value("vakit_girdi_tipi", "ezan", type=str)
        self.bip_sure = self.settings.value("bip_sure", 15, type=int)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(320, 560)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.bg = QFrame()
        self.bg.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1b26, stop:1 #24283b);
                border-radius: 20px;
                border: 1px solid #414868;
            }
        """)
        ui_layout = QVBoxLayout(self.bg)
        ui_layout.setSpacing(8)
        ui_layout.setContentsMargins(15, 15, 15, 15)

        # --- ÜST BAR ---
        top_bar = QHBoxLayout()
        self.btn_location = QPushButton("📍 Konum")
        self.btn_location.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.05); color: #7aa2f7; border-radius: 6px; padding: 4px 8px; font-weight:bold; font-size: 11px; border:none; }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: white; }
        """)
        self.btn_location.clicked.connect(self.open_location_dialog)
        top_bar.addWidget(self.btn_location)
        top_bar.addStretch()

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFixedSize(28, 28)
        self.btn_settings.setStyleSheet(
            "QPushButton { color: #c0caf5; border: none; font-size: 16px; background: transparent; } QPushButton:hover { color: white; }")
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        top_bar.addWidget(self.btn_settings)

        self.btn_info = QPushButton("?")
        self.btn_info.setFixedSize(28, 28)
        self.btn_info.setStyleSheet(
            "QPushButton { color: #c0caf5; border: 1px solid #565f89; border-radius: 14px; font-weight: bold; background: transparent; }")
        self.btn_info.clicked.connect(lambda: HakkindaDialog(self, VERSION, GITHUB_USER, REPO_NAME, WEBSITE_URL).exec())
        top_bar.addWidget(self.btn_info)
        ui_layout.addLayout(top_bar)

        # --- ŞEHİR ---
        self.lbl_loc = QLabel(self.current_city)
        self.lbl_loc.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #7aa2f7; margin-bottom: 5px; background: transparent;")
        self.lbl_loc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ui_layout.addWidget(self.lbl_loc)

        # --- TARİH ---
        date_layout = QHBoxLayout()
        self.btn_prev_day = QPushButton("<")
        self.btn_prev_day.setFixedSize(24, 24)
        self.btn_prev_day.setStyleSheet("background: #24283b; color: #7aa2f7; border-radius: 4px; font-weight:bold;")
        self.btn_prev_day.clicked.connect(lambda: self.change_date(-1))

        self.btn_date_display = QPushButton("...")
        self.btn_date_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_date_display.setStyleSheet("""
            QPushButton { 
                color: #c0caf5; font-weight: bold; font-size: 14px; border: none; background: transparent; 
                text-align: center;
            }
            QPushButton:hover { color: white; text-decoration: underline; }
        """)
        self.btn_date_display.clicked.connect(self.open_calendar)

        self.btn_next_day = QPushButton(">")
        self.btn_next_day.setFixedSize(24, 24)
        self.btn_next_day.setStyleSheet("background: #24283b; color: #7aa2f7; border-radius: 4px; font-weight:bold;")
        self.btn_next_day.clicked.connect(lambda: self.change_date(1))

        self.btn_today = QPushButton("Bugün")
        self.btn_today.setFixedHeight(24)
        self.btn_today.setStyleSheet(
            "background: #1a1b26; color: #10b981; border: 1px solid #10b981; border-radius: 4px; font-size: 10px; padding: 0 5px;")
        self.btn_today.clicked.connect(self.refresh_today)

        date_layout.addWidget(self.btn_prev_day)
        date_layout.addWidget(self.btn_date_display, 1)
        date_layout.addWidget(self.btn_next_day)
        date_layout.addWidget(self.btn_today)
        ui_layout.addLayout(date_layout)

        # --- VAKİTLER ---
        self.vakit_area = QVBoxLayout()
        self.vakit_area.setSpacing(4)
        ui_layout.addLayout(self.vakit_area)

        # --- BİLGİ ALANI ---
        ui_layout.addSpacing(15)
        self.info_area = QVBoxLayout()
        self.info_area.setSpacing(5)

        self.lbl_month_info = QLabel("")
        self.lbl_month_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_month_info.setStyleSheet(
            "color: #bb9af7; font-weight: bold; font-size: 16px; background: transparent;")
        self.info_area.addWidget(self.lbl_month_info)

        self.lbl_event_title = QLabel("")
        self.lbl_event_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_event_title.setStyleSheet("background: transparent; font-size: 15px; font-weight: bold;")
        self.lbl_event_title.setWordWrap(True)
        self.info_area.addWidget(self.lbl_event_title)

        self.ramadan_times_frame = QFrame()
        self.ramadan_times_frame.setStyleSheet("background: rgba(187, 154, 247, 0.1); border-radius: 8px;")
        self.ramadan_times_frame.hide()
        rt_layout = QHBoxLayout(self.ramadan_times_frame)
        rt_layout.setContentsMargins(5, 5, 5, 5)
        self.lbl_sahur_time = QLabel()
        self.lbl_sahur_time.setStyleSheet("color: #ff9e64; font-weight: bold; font-size:12px; background: transparent;")
        self.lbl_iftar_time = QLabel()
        self.lbl_iftar_time.setStyleSheet("color: #7dcfff; font-weight: bold; font-size:12px; background: transparent;")
        rt_layout.addWidget(self.lbl_sahur_time)
        rt_layout.addStretch()
        rt_layout.addWidget(self.lbl_iftar_time)
        self.info_area.addWidget(self.ramadan_times_frame)

        self.lbl_ramadan_timer = QLabel("")
        self.lbl_ramadan_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ramadan_timer.hide()
        self.info_area.addWidget(self.lbl_ramadan_timer)
        ui_layout.addLayout(self.info_area)
        ui_layout.addStretch()

        # --- ALT KISIM ---
        self.btn_stop_sound = QPushButton("Sesi Sustur 🔇")
        self.btn_stop_sound.hide()
        self.btn_stop_sound.clicked.connect(self.backend.stop_sound)
        self.btn_stop_sound.setStyleSheet("""
            QPushButton { background-color: #f7768e; color: white; border-radius: 6px; font-weight: bold; font-size: 12px; padding: 8px; border:none; }
            QPushButton:hover { background-color: #ff9eaf; }
        """)
        ui_layout.addWidget(self.btn_stop_sound)

        self.btn_hide = QPushButton("PENCEREYİ GİZLE")
        self.btn_hide.setFixedHeight(30)
        self.btn_hide.setStyleSheet("""
            QPushButton { 
                background: #16161e; color: #ffffff; border-radius: 6px; 
                font-weight: 900; border: 2px solid #24283b; font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover { background: #1f2335; color: #7aa2f7; border-color: #7aa2f7; }
        """)
        self.btn_hide.clicked.connect(self.hide)
        ui_layout.addWidget(self.btn_hide)
        layout.addWidget(self.bg)

    # --- EVENTLER ---
    def open_location_dialog(self):
        # Backend nesnesini LocationDialog'a gönderiyoruz
        dlg = LocationDialog(self, self.settings, self.backend)
        if dlg.exec():
            self.refresh_today()

    def open_settings_dialog(self):
        dlg = AyarlarDialog(self, self.settings)
        if dlg.exec():
            self.load_app_settings()
            self.fetch_data()

    def open_calendar(self):
        dlg = CalendarDialog(self, self.view_date)
        if dlg.exec():
            selected = dlg.get_date()
            if selected != self.view_date:
                self.view_date = selected
                self.fetch_data()

    def change_date(self, days):
        self.view_date = self.view_date.addDays(days)
        self.fetch_data()

    def refresh_today(self):
        self.view_date = QDate.currentDate()
        self.fetch_data()

    def fetch_data(self):
        self.btn_date_display.setText(self.view_date.toString("dd.MM.yyyy"))
        QApplication.processEvents()

        # Ayarlardan Konum ID'sini al (Diyanet ID)
        district_id = self.settings.value("district_id")
        city_name = self.settings.value("city_name", "")
        district_name = self.settings.value("district_name", "")

        if not district_id:
            self.current_city = "Konum Seçiniz"
            self.lbl_loc.setText(self.current_city)
            return

        self.current_city = f"{city_name} / {district_name}"
        
        # Backend'e tarih stringi gönder (API formatı: dd.MM.yyyy)
        date_str = self.view_date.toString("dd.MM.yyyy")
        data, error = self.backend.fetch_namaz_times(district_id, date_str)

        if error:
            self.lbl_loc.setText("İnternet/Veri Hatası")
            return

        self.lbl_loc.setText(f"{self.current_city}")
        t = data['timings']
        self.hijri_date = data['date']['hijri']

        # Diyanet verisi olduğu için artık offset/düzeltme yok.
        # Doğrudan veriyi kullanıyoruz.
        self.vakitler = [
            ("İmsak", t["Fajr"]),
            ("Güneş", t["Sunrise"]),
            ("Öğle", t["Dhuhr"]),
            ("İkindi", t["Asr"]),
            ("Akşam", t["Maghrib"]),
            ("Yatsı", t["Isha"])
        ]
        
        self.ramadan_times = {
            "imsak": t["Fajr"], 
            "aksam": t["Maghrib"]
        }
        self.update_special_days_info()

    def update_special_days_info(self):
        if not self.hijri_date: return

        # 1. HİCRİ AY HESAPLAMA (2026 Excel'e göre)
        d = self.view_date
        year = d.year()
        month = d.month()
        day = d.day()
        current_date = datetime.date(year, month, day)

        ay_adi = "..."
        if year == 2026:
            if current_date < datetime.date(2026, 1, 19): ay_adi = "Recep"
            elif current_date < datetime.date(2026, 2, 19): ay_adi = "Şaban"
            elif current_date < datetime.date(2026, 3, 20): ay_adi = "Ramazan"
            elif current_date < datetime.date(2026, 4, 18): ay_adi = "Şevval"
            elif current_date < datetime.date(2026, 5, 18): ay_adi = "Zilkade"
            elif current_date < datetime.date(2026, 6, 16): ay_adi = "Zilhicce"
            elif current_date < datetime.date(2026, 7, 16): ay_adi = "Muharrem"
            elif current_date < datetime.date(2026, 8, 14): ay_adi = "Safer"
            elif current_date < datetime.date(2026, 9, 13): ay_adi = "Rebiülevvel"
            elif current_date < datetime.date(2026, 10, 12): ay_adi = "Rebiülahir"
            elif current_date < datetime.date(2026, 11, 11): ay_adi = "Cemaziyelevvel"
            else: ay_adi = "Cemaziyelahir"
        else:
            # Emushaf API hicri tarihi bazen veriyor bazen vermiyor, 
            # ancak biz backend'de basic bir map yaptık.
            h_month = self.hijri_date['month']
            # Eğer API ay ismini metin olarak verdiyse onu kullan, yoksa sayıdan bul
            if isinstance(h_month, dict) and h_month.get("en"):
                ay_adi = h_month.get("en")
            else:
                # Yedek (Basit Liste)
                ay_adi = "Hicri Takvim"

        self.lbl_month_info.setText(f"🌙 {ay_adi} Ayındayız")
        self.lbl_month_info.show()

        # 2. ÖZEL GÜN KONTROLÜ
        key_nat = (month, day)
        key_rel = (month, day)

        best_name = None
        is_national = False

        if key_nat in NATIONAL_HOLIDAYS:
            best_name = NATIONAL_HOLIDAYS[key_nat]
            is_national = True
        elif year == 2026 and key_rel in RELIGIOUS_HOLIDAYS_2026:
            best_name = RELIGIOUS_HOLIDAYS_2026[key_rel]

        if best_name:
            self.lbl_event_title.setText(f"Bugün {best_name}!")
            color = "#ff5555" if is_national else "#50fa7b"
            self.lbl_event_title.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 15px; background: transparent;")
            self.lbl_event_title.show()
        else:
            self.lbl_event_title.hide()

        # Ramazan Sayacı
        self.is_ramadan = (ay_adi == "Ramazan")
        if self.is_ramadan:
            self.ramadan_times_frame.show()
            self.lbl_sahur_time.setText(f"Sahur: {self.ramadan_times.get('imsak')}")
            self.lbl_iftar_time.setText(f"İftar: {self.ramadan_times.get('aksam')}")
        else:
            self.ramadan_times_frame.hide()
            self.lbl_ramadan_timer.hide()

    def update_logic(self):
        if not self.vakitler: return
        now = datetime.datetime.now()
        is_today = (self.view_date == QDate.currentDate())

        self.clear_layout(self.vakit_area)
        next_idx = 0

        if is_today:
            for i, (name, t_str) in enumerate(self.vakitler):
                v_dt = datetime.datetime.combine(now.date(), datetime.datetime.strptime(t_str, "%H:%M").time())
                if v_dt > now:
                    next_idx = i
                    break
                if i == 5 and v_dt < now: next_idx = 0

            yatsi_time = datetime.datetime.combine(now.date(),
                                                   datetime.datetime.strptime(self.vakitler[5][1], "%H:%M").time())
            start_idx = 5 if now > yatsi_time else max(0, next_idx - 1)
        else:
            start_idx = 0
            next_idx = -1

        display_list = self.vakitler[start_idx:] if is_today else self.vakitler

        for i, (name, t_str) in enumerate(display_list):
            original_idx = start_idx + i if is_today else i
            v_dt = datetime.datetime.combine(now.date(), datetime.datetime.strptime(t_str, "%H:%M").time())
            is_passed = (v_dt < now) if is_today else False
            is_next = (original_idx == next_idx) and not is_passed and is_today

            h, m, s = 0, 0, 0
            right_text = ""
            is_highlighted = False

            if is_today:
                if is_passed:
                    right_text = "Vaktindeyiz !!"
                    is_highlighted = True
                else:
                    diff = v_dt - now
                    total_sec = int(diff.total_seconds())
                    h, rem = divmod(total_sec, 3600)
                    m, s = divmod(rem, 60)

                    time_str = f"{m}dk {s}sn"
                    if h > 0:
                        time_str = f"{h}sa " + time_str

                    right_text = f"{time_str} kaldı"
                    is_highlighted = False

            self.add_row((name, t_str), right_text, is_highlighted, is_passed)

            if is_next and is_today:
                if h == 0 and m == self.uyari_dk and s == 0: self.bildir(name, "uyari")
                if h == 0 and m == 0 and s == 0: self.bildir(name, "vakit_girdi")

        if self.is_ramadan and is_today: self.update_ramadan_timer(now)

    def add_row(self, data, right_text, highlight, is_past):
        row = QFrame()
        style = "background: rgba(36, 40, 59, 0.6); border: none;"
        txt_color = "#9aa5ce"
        name_color = "#c0caf5"
        time_color = "#c0caf5"

        if highlight:
            style = "background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981;"
            txt_color = "#10b981"
            name_color = "#10b981"
            time_color = "#10b981"
        elif is_past:
            style = "background: rgba(255, 255, 255, 0.02); border: none;"
            txt_color = "#414868"
            name_color = "#565f89"
            time_color = "#565f89"

        row.setStyleSheet(f"QFrame {{ {style} border-radius: 6px; }}")
        row.setFixedHeight(34)
        lyt = QHBoxLayout(row)
        lyt.setContentsMargins(8, 0, 8, 0)

        nm = QLabel(data[0])
        nm.setStyleSheet(
            f"color: {name_color}; font-weight: bold; font-size: 12px; border:none; background:transparent;")

        rt = QLabel(right_text)
        if right_text == "Vaktindeyiz !!":
            rt.setStyleSheet("color: #ffffff; font-weight: 900; font-size: 11px; border:none; background:transparent;")
        else:
            rt.setStyleSheet(
                f"color: {txt_color}; font-size: 10px; font-weight: bold; border:none; background:transparent;")

        tm = QLabel(data[1])
        tm.setStyleSheet(
            f"color: {time_color}; font-weight: bold; font-size: 13px; border:none; background:transparent;")

        lyt.addWidget(nm)
        lyt.addStretch()
        lyt.addWidget(rt)
        lyt.addStretch()
        lyt.addWidget(tm)
        self.vakit_area.addWidget(row)

    def bildir(self, name, tip):
        title = "Vakit Hatırlatma" if tip == "uyari" else "Vakit Girdi"
        msg = f"{name} vaktine {self.uyari_dk} dk kaldı." if tip == "uyari" else f"{name} vakti girdi."
        self.tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 0)

        if not self.ses_aktif: return

        if tip == "uyari":
            self.backend.play_sound("alarm", duration_sec=self.bip_sure)
        elif tip == "vakit_girdi":
            if self.vakit_girdi_tipi == "ezan":
                self.backend.play_sound("ezan", is_morning=(name == "İmsak"), is_sun=(name == "Güneş"))
            else:
                self.backend.play_sound("alarm", duration_sec=self.bip_sure)

    def create_autostart_entry(self):
        try:
            path = os.path.expanduser("~/.config/autostart/namazvakti.desktop")
            if not os.path.exists(os.path.dirname(path)): return
            cmd = sys.executable if getattr(sys, 'frozen',
                                            False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
            with open(path, "w") as f:
                f.write(
                    f"[Desktop Entry]\nType=Application\nExec={cmd}\nHidden=false\nX-GNOME-Autostart-enabled=true\nName=Namaz Vakti\nIcon={LOGO_PATH}")
        except:
            pass

    # --- SÜRÜKLE BIRAK (WAYLAND & X11 HİBRİT ÇÖZÜM) ---
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # 1. YÖNTEM: Wayland (GNOME/KDE) Native Sürükleme
            if self.windowHandle() and hasattr(self.windowHandle(), 'startSystemMove'):
                if self.windowHandle().startSystemMove():
                    return # Başarılı olduysa fonksiyondan çık

            # 2. YÖNTEM: X11 (Fallback)
            # Wayland başarısız olursa veya X11 ise manuel hesaplama yap
            self.m_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        # Sadece X11'de çalışır (Wayland'de m_pos set edilmezse buraya girmez)
        if e.buttons() == Qt.MouseButton.LeftButton and self.m_pos:
            self.move(e.globalPosition().toPoint() - self.m_pos)
            
    def mouseReleaseEvent(self, e):
        self.m_pos = None # Sürükleme bitti

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal(); self.activateWindow()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self.app_icon, self)
        menu = QMenu()
        menu.setStyleSheet("QMenu { background: #1a1b26; color: #c0caf5; border: 1px solid #414868; }")
        show_action = QAction("Göster/Gizle", self)
        show_action.triggered.connect(self.toggle_window)
        menu.addAction(show_action)
        quit_action = QAction("Çıkış", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.toggle_window() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # --- LINUX SİMGE VE GRUPLAMA DÜZELTMESİ ---
    app.setDesktopFileName("namazvakti")

    # --- SINGLE INSTANCE (TEKİL ÇALIŞMA) ---
    lock_file_path = os.path.join(QDir.tempPath(), "namazvakti_v1.lock")
    lock_file = QLockFile(lock_file_path)
    
    if lock_file.isLocked():
        lock_file.removeStaleLockFile()

    if not lock_file.tryLock(100):
        sys.exit(0)

    window = NamazHUD()
    window.show()
    
    exit_code = app.exec()
    
    del lock_file 
    sys.exit(exit_code)