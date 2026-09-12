#!/data/data/com.termux/files/usr/bin/bash
echo "========================================================="
echo "   Android Termux Setup for Mobile PDF Generator"
echo "========================================================="
echo ""
echo "Step 1: Updating packages..."
pkg update -y && pkg upgrade -y

echo "Step 2: Installing Python and build dependencies..."
pkg install python python-pip libjpeg-turbo freetype -y

echo "Step 3: Installing required Python packages..."
pip install --upgrade pip
pip install openpyxl pandas Pillow xhtml2pdf requests

echo ""
echo "✅ Setup Complete!"
echo "To run the generator, type: python mobile_pdf_maker.py"
echo "========================================================="
