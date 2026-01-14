#!/bin/bash

# Hata olursa durdur
set -e

# --- PROJE BİLGİLERİ ---
APP_NAME="namazvakti"
VERSION="1.0"
ARCH="amd64"
MAINTAINER="Tarik Vardar <tarikvardar@gmail.com>"
WEBSITE="https://www.tarikvardar.com.tr"
DESCRIPTION="Linux sistemler icin modern namaz vakti takip araci."
LICENSE="MIT License"

# --- KLASÖR TANIMLARI ---
WORK_DIR="build_deb"
OUTPUT_DEB="${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "--------------------------------------------------------"
echo "🚀 NAMAZ VAKTİ PAKETLEME SİHİRBAZI (v$VERSION)"
echo "--------------------------------------------------------"

# 1. SİSTEM BAĞIMLILIKLARINI KONTROL ET VE YÜKLE (Derleme Ortamı İçin)
echo "📦 Derleme için gerekli sistem paketleri kontrol ediliyor..."
sudo apt-get update -qq
# Qt6 ve PyInstaller'ın sağlıklı çalışması için gerekli kütüphaneler
sudo apt-get install -y python3-venv python3-pip binutils \
    libxcb-cursor0 libxcb-xinerama0 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 \
    libegl1 libopengl0 libxkbcommon-x11-0 libdbus-1-3 \
    libgstreamer1.0-0 gstreamer1.0-plugins-good

# 2. SANAL ORTAM (VENV) OLUŞTURMA
# Debian 12/Pardus 23 "externally-managed-environment" hatasını aşmak için en güvenli yol.
echo "🐍 Python Sanal Ortamı (venv) hazırlanıyor..."
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate

# 3. BAĞIMLILIKLARI YÜKLE
echo "⬇️ Python kütüphaneleri sanal ortama kuruluyor..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4. PYINSTALLER İLE DERLEME
echo "🔨 PyInstaller ile Binary (.bin) oluşturuluyor..."

# Temizlik
rm -rf build dist $WORK_DIR *.spec

# --onefile: Tek dosya çıktı (daha temiz dağıtım)
# --windowed: Konsol penceresi açılmaz
pyinstaller --noconfirm --onefile --windowed --clean \
    --name "$APP_NAME" \
    --add-data "assets:assets" \
    --icon "assets/logo.png" \
    --hidden-import "PyQt6" \
    --collect-all "requests" \
    main.py

# Sanal ortamdan çık
deactivate

# 5. DEBIAN PAKET YAPISINI KURMA
echo "📂 .deb paket yapısı oluşturuluyor..."
mkdir -p $WORK_DIR/usr/bin
mkdir -p $WORK_DIR/usr/share/applications
mkdir -p $WORK_DIR/usr/share/icons/hicolor/512x512/apps
mkdir -p $WORK_DIR/DEBIAN

# Binary dosyasını taşı ve izin ver
cp dist/$APP_NAME $WORK_DIR/usr/bin/
chmod 755 $WORK_DIR/usr/bin/$APP_NAME

# Logoyu taşı
if [ -f "assets/logo.png" ]; then
    cp assets/logo.png $WORK_DIR/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png
else
    echo "⚠️ UYARI: assets/logo.png bulunamadı!"
fi

# 6. .DESKTOP DOSYASI (Menü Entegrasyonu)
echo "📝 Desktop dosyası yazılıyor..."
cat <<EOF > $WORK_DIR/usr/share/applications/$APP_NAME.desktop
[Desktop Entry]
Name=Namaz Vakti HUD
Comment=Namaz Vakitleri Takip Uygulaması
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;Qt;Education;
StartupWMClass=namazvakti
Keywords=namaz;vakit;ezan;diyanet;
StartupNotify=true
EOF
chmod 644 $WORK_DIR/usr/share/applications/$APP_NAME.desktop

# 7. CONTROL DOSYASI (Gelişmiş Bağımlılıklar ile)
# 'Depends' kısmına ses ve grafik kütüphaneleri eklendi.
echo "📝 Control dosyası yazılıyor..."
cat <<EOF > $WORK_DIR/DEBIAN/control
Package: $APP_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: $MAINTAINER
Section: utils
Priority: optional
Homepage: $WEBSITE
Depends: libc6, libasound2, libgl1, libegl1, libxkbcommon-x11-0, libxcb-cursor0, libgstreamer1.0-0, gstreamer1.0-plugins-good
Description: $DESCRIPTION
 Pardus, Debian ve Ubuntu tabanlı sistemler için geliştirilmiş;
 şeffaf, modern ve HUD tasarımlı namaz vakti takip aracı.
 .
 Özellikler:
 - Diyanet/Emushaf uyumlu veriler
 - Ezan ve sesli uyarı sistemi
 - Hicri takvim ve dini günler
 - Sistem tepsisi (Tray) desteği
 Lisans: $LICENSE
EOF
chmod 755 $WORK_DIR/DEBIAN/control

# 8. PAKETLEME
echo "📦 .deb paketi paketleniyor..."
dpkg-deb --build $WORK_DIR $OUTPUT_DEB

# 9. SON TEMİZLİK (İsteğe bağlı, venv kalabilir)
# rm -rf venv build dist $WORK_DIR *.spec

echo ""
echo "✅ İŞLEM BAŞARIYLA TAMAMLANDI!"
echo "📂 Paket: $OUTPUT_DEB"
echo "ℹ️  Kurulum için: sudo dpkg -i $OUTPUT_DEB"