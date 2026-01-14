import os
import json
import requests
import datetime
from PyQt6.QtCore import QUrl, QTimer, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from tasarim import CACHE_PATH, SOUND_PATH_BIP, SOUND_PATH_EZAN, SOUND_PATH_SABAHEZAN

# Emushaf API Endpoints
API_BASE = "https://ezanvakti.emushaf.net"

class NamazBackend(QObject):
    def __init__(self):
        super().__init__()
        self.data_cache = {}
        self.load_cache()
        
        # Medya Oynatıcı
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        self.stop_btn_ref = None

    # --- CACHE YÖNETİMİ ---
    def load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self.data_cache = json.load(f)
            except:
                self.data_cache = {}

    def save_cache(self):
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data_cache, f, ensure_ascii=False)
        except:
            pass

    # --- KONUM VERİLERİ (API) ---
    def get_countries(self):
        """Ülke listesini çeker."""
        try:
            resp = requests.get(f"{API_BASE}/ulkeler", timeout=5)
            if resp.status_code == 200:
                return resp.json(), None
            return [], "Veri alınamadı"
        except Exception as e:
            return [], str(e)

    def get_cities(self, country_id):
        """Seçilen ülkenin şehirlerini çeker."""
        try:
            resp = requests.get(f"{API_BASE}/sehirler/{country_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json(), None
            return [], "Veri alınamadı"
        except Exception as e:
            return [], str(e)

    def get_districts(self, city_id):
        """Seçilen şehrin ilçelerini çeker."""
        try:
            resp = requests.get(f"{API_BASE}/ilceler/{city_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json(), None
            return [], "Veri alınamadı"
        except Exception as e:
            return [], str(e)

    # --- VAKİT VERİLERİ ---
    def fetch_namaz_times(self, district_id, date_str):
        """
        Belirtilen ilçe ID'si için vakitleri getirir.
        date_str formatı: "dd.MM.yyyy" (Örn: 14.01.2026)
        """
        # Cache Key: ilceID_Ay_Yil (API aylık veri döndüğü için cache key'i aylık yapıyoruz)
        try:
            day, month, year = date_str.split('.')
            cache_key = f"times_{district_id}_{month}_{year}"
        except:
            return None, "Tarih formatı hatası"

        # 1. Önce Cache'e bak
        if cache_key in self.data_cache:
            monthly_data = self.data_cache[cache_key]
            day_data = self.find_day_in_list(monthly_data, date_str)
            if day_data:
                return self.map_to_internal_format(day_data), None

        # 2. Cache'de yoksa API'den çek (API 30 günlük veri döner)
        try:
            resp = requests.get(f"{API_BASE}/vakitler/{district_id}", timeout=5)
            if resp.status_code == 200:
                data_list = resp.json()
                
                # Veriyi cache'e kaydet
                self.data_cache[cache_key] = data_list
                self.save_cache()

                # İstenen günü bul
                day_data = self.find_day_in_list(data_list, date_str)
                if day_data:
                    return self.map_to_internal_format(day_data), None
                else:
                    return None, "Seçilen tarih için veri bulunamadı."
            else:
                return None, f"API Hatası: {resp.status_code}"

        except Exception as e:
            return None, f"Bağlantı Hatası: {str(e)}"

    def find_day_in_list(self, data_list, target_date_str):
        """API'den gelen liste içinde hedef tarihi bulur."""
        for item in data_list:
            # API 'MiladiTarihKisa' dönüyor: "14.01.2026"
            if item.get("MiladiTarihKisa") == target_date_str:
                return item
        return None

    def map_to_internal_format(self, api_data):
        """
        Emushaf (Diyanet) verisini, uygulamanın beklediği Aladhan formatına çevirir.
        Böylece Main.py'de değişiklik yapmamıza gerek kalmaz.
        """
        return {
            "timings": {
                "Fajr": api_data["Imsak"],
                "Sunrise": api_data["Gunes"],
                "Dhuhr": api_data["Ogle"],
                "Asr": api_data["Ikindi"],
                "Maghrib": api_data["Aksam"],
                "Isha": api_data["Yatsi"]
            },
            "date": {
                "hijri": {
                    "month": {
                        # API Hicri ayı metin veya sayı dönebilir, basit bir mapping
                        "number": 1, # Varsayılan (Main.py zaten tarihi kendi hesaplıyor)
                        "en": api_data.get("HicriTarihUzun", "") 
                    },
                    "day": api_data.get("HicriTarihKisa", "").split('.')[0] if "HicriTarihKisa" in api_data else "1"
                }
            }
        }

    # --- SES ÇALMA ---
    def play_sound(self, sound_type, duration_sec=0, is_morning=False, is_sun=False):
        self.player.stop()
        file_path = SOUND_PATH_BIP
        loop_count = QMediaPlayer.Loops.Infinite

        if sound_type == "ezan" and not is_sun:
            file_path = SOUND_PATH_SABAHEZAN if is_morning else SOUND_PATH_EZAN
            loop_count = 1

        if os.path.exists(file_path):
            self.player.setSource(QUrl.fromLocalFile(os.path.abspath(file_path)))
            self.player.setLoops(loop_count)
            if sound_type != "ezan" and duration_sec > 0:
                QTimer.singleShot(duration_sec * 1000, self.stop_sound)
            self.player.play()
            if self.stop_btn_ref: self.stop_btn_ref.show()

    def stop_sound(self):
        self.player.stop()
        if self.stop_btn_ref: self.stop_btn_ref.hide()