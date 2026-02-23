#!/bin/bash
echo "Installing Python and dependencies..."

# Update system
apt-get update

# Install Python3 and pip
apt-get install -y python3 python3-pip

# Install dependencies with pip
python3 -m pip install -r requirements.txt

echo "✅ Python and dependencies installation complete!"
