# 🕌 Namaz Vakti v1.0

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Pardus%20%7C%20Debian%20%7C%20Linux-orange.svg)

Linux masaüstü ortamları için geliştirilmiş; şeffaf, modern ve kullanıcı dostu Namaz Vakti görüntüleme aracı.

## 📸 Ekran Görüntüleri

| **Ana Ekran (HUD)** | **Ayarlar** |
|:---:|:---:|
| ![Ana Ekran](screenshots/1.png) | ![Takvim](screenshots/2.png) |
| *Şeffaf ve Taşınabilir Panel* | *Ayarlar Paneli* |

## ✨ Özellikler

* **Tam Uyumlu Vakitler:** Diyanet vakitleri uyumlu ülke/il/ilçe bazlı veri.
* **Sesli Uyarı:** Ezan, alarm veya sessiz mod seçenekleri. Sabah ezanı, Vakit ezanı, Bip alarm
* **HUD Tasarımı:** Masaüstünde yer kaplamayan şeffaf yapı.
* **Hicri Takvim:** Dini günler ve resmi tatiller renkli takvimde.
* **Hatırlatma:** Vakite istenilen süre kadar kalan zaman da istenilen süre boyunca bip alarm ve baloncuk uyarı
* **Güncelleme:** Hakkında kısmından güncelleme kontrolü
* **Takvim:** Belirlenen bir günün vakitlerini gösterme

## 📦 Kurulum

### Yöntem 1: .deb Paketi (Önerilen)
Releases sayfasından en son sürümü indirin:
```bash
sudo dpkg -i namazvakti_1.0_amd64.deb
sudo apt-get install -f  # Eksik bağımlılık varsa
```

### Yöntem 2: Kaynak Koddan Çalıştırma
```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python3 main.py
```

## ⚖️ Lisans
Bu proje **MIT Lisansı** ile lisanslanmıştır.
Copyright (c) 2026 Tarık Vardar

## Web Sitem 🌐
[www.tarikvardar.com.tr](https://www.tarikvardar.com.tr)
