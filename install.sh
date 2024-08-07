echo "========================================================================="
echo "INSTALLATION SCRIPT for NVIDIA libs"
echo "========================================================================="

echo "INFO on capabilities ..."
echo "    $(lspci | grep -i nvidia)"

echo "INSTALL base system ..."
sudo apt-get update
sudo apt -y install ubuntu-drivers-common


sudo ubuntu-drivers autoinstall

# Check if a reboot is necessary
if nvidia-smi; then
    echo "INFO nvidia-smi ..."
    nvidia-smi
else
    echo "RESTART required: NVIDIA drivers are not install. Please reboot and restart the script"
    exit 
fi

echo "INSTALL CUDA for NVIDIA ..."
sudo apt -y install nvidia-cuda-toolkit


echo "INSTALL Docker ..."

if [ ! -f get-docker.sh ]; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh
fi

echo "Install containers for NVIDIA ..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt -y install nvidia-container-toolkit

echo "INSTALLATION done!"