import sys
import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QFrame, QMessageBox,
                             QSlider, QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt

# Backend referansı için import etmeyeceğiz, parametre olarak alacağız veya main'den yöneteceğiz.
# Ancak LocationDialog içinde basit request işlemleri için backend metodlarına ihtiyacımız var.
# Döngüsel import olmaması için main'den backend nesnesini parametre olarak alacağız.

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Yollar
LOGO_PATH = resource_path(os.path.join("assets", "logo.png"))
SOUND_PATH_BIP = resource_path(os.path.join("assets", "bip.ogg"))
SOUND_PATH_EZAN = resource_path(os.path.join("assets", "ezan.ogg"))
SOUND_PATH_SABAHEZAN = resource_path(os.path.join("assets", "sabahezan.ogg"))
CACHE_PATH = resource_path("prayer_cache.json")


# --- AYARLAR DİYALOĞU ---
class AyarlarDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Ayarlar")
        self.setFixedSize(320, 350) # Offset kalktığı için boyutu kısalttık
        self.setStyleSheet("""
            QDialog { background-color: #1a1b26; color: #c0caf5; }
            QLabel { color: #c0caf5; font-weight: bold; font-size: 12px; }
            QCheckBox { color: #c0caf5; font-weight: bold; }
            QComboBox, QSpinBox { 
                background: #24283b; border: 1px solid #414868; 
                padding: 5px; color: white; border-radius: 4px;
            }
            QSlider::groove:horizontal { height: 4px; background: #24283b; border-radius: 2px; }
            QSlider::handle:horizontal { background: #bb9af7; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QPushButton { padding: 8px; border-radius: 4px; font-weight:bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Ses Açma/Kapama
        self.cb_audio = QCheckBox("Sesli Bildirimleri Etkinleştir")
        self.cb_audio.setChecked(self.settings.value("audio_enabled", True, type=bool))
        layout.addWidget(self.cb_audio)

        # Ayırıcı
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #414868;")
        layout.addWidget(line)

        # 2. Vakit Girince Ne Çalsın?
        layout.addWidget(QLabel("Vakit Girdiğinde:"))
        self.combo_giris = QComboBox()
        self.combo_giris.addItem("🕌 Ezan Oku", "ezan")
        self.combo_giris.addItem("🔔 Alarm Çal", "alarm")
        current_type = self.settings.value("vakit_girdi_tipi", "ezan", type=str)
        index = self.combo_giris.findData(current_type)
        if index >= 0: self.combo_giris.setCurrentIndex(index)
        layout.addWidget(self.combo_giris)

        # 3. Alarm Süresi
        h_layout_sure = QHBoxLayout()
        h_layout_sure.addWidget(QLabel("Alarm/Bip Süresi:"))
        self.lbl_sure_val = QLabel("15 sn")
        self.lbl_sure_val.setStyleSheet("color: #bb9af7;")
        h_layout_sure.addStretch()
        h_layout_sure.addWidget(self.lbl_sure_val)
        layout.addLayout(h_layout_sure)

        self.sld_bip_sure = QSlider(Qt.Orientation.Horizontal)
        self.sld_bip_sure.setRange(5, 60)
        self.sld_bip_sure.setValue(self.settings.value("bip_sure", 15, type=int))
        self.sld_bip_sure.valueChanged.connect(lambda v: self.lbl_sure_val.setText(f"{v} sn"))
        self.lbl_sure_val.setText(f"{self.sld_bip_sure.value()} sn")
        layout.addWidget(self.sld_bip_sure)

        # 4. Hatırlatma Süresi
        h_layout_uyari = QHBoxLayout()
        h_layout_uyari.addWidget(QLabel("Vakit Hatırlatma:"))
        self.lbl_uyari_val = QLabel("15 dk kala")
        self.lbl_uyari_val.setStyleSheet("color: #ff9e64;")
        h_layout_uyari.addStretch()
        h_layout_uyari.addWidget(self.lbl_uyari_val)
        layout.addLayout(h_layout_uyari)

        self.sld_uyari = QSlider(Qt.Orientation.Horizontal)
        self.sld_uyari.setRange(1, 60)
        self.sld_uyari.setValue(self.settings.value("warning_min", 15, type=int))
        self.sld_uyari.valueChanged.connect(lambda v: self.lbl_uyari_val.setText(f"{v} dk kala"))
        self.lbl_uyari_val.setText(f"{self.sld_uyari.value()} dk kala")
        layout.addWidget(self.sld_uyari)

        layout.addStretch()

        # Kaydet Butonu
        btn_save = QPushButton("Kaydet ve Kapat")
        btn_save.setStyleSheet("background: #10b981; color: white;")
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

    def save_settings(self):
        self.settings.setValue("audio_enabled", self.cb_audio.isChecked())
        self.settings.setValue("vakit_girdi_tipi", self.combo_giris.currentData())
        self.settings.setValue("bip_sure", self.sld_bip_sure.value())
        self.settings.setValue("warning_min", self.sld_uyari.value())
        self.accept()


# --- KONUM SEÇİM DİYALOĞU (YENİ - API TABANLI) ---
class LocationDialog(QDialog):
    def __init__(self, parent=None, settings=None, backend=None):
        super().__init__(parent)
        self.settings = settings
        self.backend = backend # Backend nesnesini kullanacağız
        self.setWindowTitle("Konum Ayarları")
        self.setFixedSize(320, 300)
        self.setStyleSheet("""
            QDialog { background-color: #1a1b26; color: #c0caf5; }
            QLabel { color: #c0caf5; font-weight: bold; }
            QComboBox { 
                background: #24283b; border: 1px solid #414868; 
                padding: 5px; color: white; border-radius: 4px;
            }
            QComboBox::drop-down { border:none; }
            QPushButton { padding: 8px; border-radius: 4px; font-weight:bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Konum Seçimi (Diyanet Uyumlu)"))

        # Ülke
        layout.addWidget(QLabel("Ülke:"))
        self.combo_country = QComboBox()
        self.combo_country.currentIndexChanged.connect(self.load_cities)
        layout.addWidget(self.combo_country)

        # Şehir
        layout.addWidget(QLabel("Şehir:"))
        self.combo_city = QComboBox()
        self.combo_city.currentIndexChanged.connect(self.load_districts)
        layout.addWidget(self.combo_city)

        # İlçe
        layout.addWidget(QLabel("İlçe:"))
        self.combo_district = QComboBox()
        layout.addWidget(self.combo_district)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Kaydet")
        btn_save.setStyleSheet("background: #10b981; color: white;")
        btn_save.clicked.connect(self.save_and_close)

        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background: #f7768e; color: white;")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        # Başlangıç verilerini yükle
        self.load_initial_data()

    def load_initial_data(self):
        """Ülkeleri yükler ve kayıtlı seçimi getirir."""
        if not self.backend: return
        
        # Ülkeleri Çek
        self.combo_country.addItem("Yükleniyor...", None)
        countries, error = self.backend.get_countries()
        
        self.combo_country.clear()
        if error:
            self.combo_country.addItem(f"Hata: {error}")
            return

        # Ülkeleri sırala (Türkiye en başa)
        turkey = None
        others = []
        for c in countries:
            if c['UlkeAdi'] == "TÜRKİYE":
                turkey = c
            else:
                others.append(c)
        
        # Türkçe karakter sıralaması için basit key
        others.sort(key=lambda x: x['UlkeAdi'])
        
        if turkey: self.combo_country.addItem(turkey['UlkeAdi'], turkey['UlkeID'])
        for c in others:
            self.combo_country.addItem(c['UlkeAdi'], c['UlkeID'])

        # Önceden kayıtlı veri varsa seçmeye çalış (Sadece ülke bazlı değil, genel mantık)
        # Varsayılan Türkiye seçili gelsin (Index 0)
        self.combo_country.setCurrentIndex(0) 

    def load_cities(self):
        """Seçilen ülkeye göre şehirleri yükler."""
        country_id = self.combo_country.currentData()
        if not country_id: return

        self.combo_city.clear()
        self.combo_city.addItem("Yükleniyor...", None)
        
        cities, error = self.backend.get_cities(country_id)
        self.combo_city.clear()
        
        if error:
            self.combo_city.addItem("Hata", None)
            return

        for city in cities:
            self.combo_city.addItem(city['SehirAdi'], city['SehirID'])

        # Kayıtlı şehir varsa seç (Opsiyonel geliştirilebilir)

    def load_districts(self):
        """Seçilen şehre göre ilçeleri yükler."""
        city_id = self.combo_city.currentData()
        if not city_id: return

        self.combo_district.clear()
        self.combo_district.addItem("Yükleniyor...", None)
        
        districts, error = self.backend.get_districts(city_id)
        self.combo_district.clear()
        
        if error:
            self.combo_district.addItem("Hata", None)
            return

        for dist in districts:
            self.combo_district.addItem(dist['IlceAdi'], dist['IlceID'])

    def save_and_close(self):
        district_id = self.combo_district.currentData()
        district_name = self.combo_district.currentText()
        city_name = self.combo_city.currentText()
        country_name = self.combo_country.currentText()

        if district_id:
            self.settings.setValue("district_id", district_id)
            self.settings.setValue("district_name", district_name)
            self.settings.setValue("city_name", city_name)
            self.settings.setValue("country_name", country_name)
            # Eski manuel koordinat verilerini temizleyebiliriz veya bırakabiliriz
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir ilçe seçiniz.")