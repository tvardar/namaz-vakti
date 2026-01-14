#!/bin/bash

# Hata olursa durdur
set -e

# --- AYARLAR ---
REPO_URL="https://github.com/tvardar/namaz-vakti.git"
COMMIT_MSG="Namaz Vakti v1.0 - Kararlı Sürüm Yayını 🚀"
GIT_NAME="Tarık Vardar"
GIT_EMAIL="tarikvardar@gmail.com"
YEAR="2026"

echo "🚀 GitHub Dağıtım Süreci Başlatılıyor..."

# 1. TEMİZLİK (Eski derleme artıkları temizleniyor)
echo "🧹 Gereksiz derleme dosyaları temizleniyor..."
rm -rf __pycache__ build dist venv *.spec prayer_cache.json build_deb *.deb

# Git geçmişi sıfırlama (İsteğe bağlı - eğer sıfırdan repo kuruyorsanız)
if [ -d ".git" ]; then
    echo "⚠️ .git klasörü bulundu, siliniyor ve yeniden başlatılıyor..."
    rm -rf .git
fi

# 2. GIT BAŞLATMA
git init
git config user.name "$GIT_NAME"
git config user.email "$GIT_EMAIL"
git branch -M main
git remote add origin $REPO_URL

# 3. .gitignore OLUŞTURMA (GÜNCELLENDİ)
# Yeni paketleme sistemine uygun ignore listesi
cat <<EOF > .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env

# Paketleme / Derleme
build/
dist/
build_deb/
*.spec
*.deb

# IDE / Editör
.idea/
.vscode/
*.swp

# Uygulama Verileri
prayer_cache.json
assets/cities.json
*.lock

# Scriptler (İsteğe bağlı - repoda saklamak isterseniz bunları çıkarın)
# deploy_namazvakti.sh
# paketle_namazvakti.sh
EOF

# 4. README.md OLUŞTURMA
cat <<EOF > README.md
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
\`\`\`bash
sudo dpkg -i namazvakti_1.0_amd64.deb
sudo apt-get install -f  # Eksik bağımlılık varsa
\`\`\`

### Yöntem 2: Kaynak Koddan Çalıştırma
\`\`\`bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python3 main.py
\`\`\`

## ⚖️ Lisans
Bu proje **MIT Lisansı** ile lisanslanmıştır.
Copyright (c) $YEAR $GIT_NAME

## Web Sitem 🌐
[www.tarikvardar.com.tr](https://www.tarikvardar.com.tr)
EOF

# 5. LICENSE DOSYASI OLUŞTURMA
cat <<EOF > LICENSE
MIT License

Copyright (c) $YEAR $GIT_NAME

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 6. GÖNDERİM
echo "📦 Dosyalar staging alanına ekleniyor..."
git add .

echo "💾 Commit oluşturuluyor..."
git commit -m "$COMMIT_MSG"

echo "🚀 GitHub'a ZORLA (Force) gönderiliyor..."
git push --force -u origin main

echo "✅ Dağıtım Süreci Tamamlandı!"