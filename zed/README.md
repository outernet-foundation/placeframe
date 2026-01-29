A) Verify your JetPack/L4T (so you pick the right SDK)
head -n1 /etc/nv_tegra_release

# or

dpkg-query --show nvidia-l4t-core
You’ll use that L4T/JetPack number on the ZED download page to pick the matching installer. (ZED SDK installers are per-JetPack/L4T.)
stereolabs.com

In a desktop browser, open Stereolabs → Downloads → ZED SDK → NVIDIA Jetson, pick the exact JetPack/L4T you saw above, and copy the download URL.

cd ~
wget --content-disposition '<PASTE_THE_ZED_SDK_JETSON_URL_HERE>'

chmod +x ZED_SDK_Tegra_L4T*.run
sudo ./ZED_SDK_Tegra_L4T*.run -- silent

later

# 1) stash the helper somewhere you own

mkdir -p ~/.local/share/pyzed
sudo cp /usr/local/zed/get_python_api.py ~/.local/share/pyzed/
sudo chown "$USER":"$USER" ~/.local/share/pyzed/get_python_api.py
cd ~/.local/share/pyzed

uv init
uv add pip cython numpy requests
uv run get_python_api.py

then find the wheel and vendor it

sudo useradd --system --no-create-home --shell /usr/sbin/nologin zed_service
sudo usermod -aG zed,video "$USER"
sudo usermod -aG zed,video zed_service
newgrp video
newgrp zed

curl -Ls https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh

sudo mkdir -p /home/zed_service
sudo chown -R zed_service:zed /home/zed_service
sudo chmod 750 /home/zed_service

sudo chmod +x /opt/plerion/capture-app/zed/start.sh
sudo cp /opt/plerion/capture-app/zed/zed-capture.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now zed-capture.service

to tail logs:
sudo journalctl -u <service>.service -f