#!/bin/bash

echo "🚀 Menyiapkan lingkungan..."

# Update system
apt update && apt upgrade -y

# Install Python & tools
apt install -y python3 python3-pip git screen

# Install requirements
pip3 install -r requirements.txt

# Jalankan bot dalam screen
screen -dmS userbot python3 bot.py

echo "✅ Bot dijalankan dalam screen bernama 'userbot'"
