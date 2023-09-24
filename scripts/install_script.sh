#!/bin/bash

# Update and upgrade packages
sudo apt update
sudo apt upgrade -y
# Add a repository for Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.10 and pip
sudo apt install python3.10 python3-pip -y
# Create symlinks for python and pip
sudo ln -s /usr/bin/python3.10 /usr/local/bin/python
sudo ln -s /usr/bin/pip3 /usr/local/bin/pip

# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p ~/miniconda
rm ~/miniconda.sh
source ~/miniconda/etc/profile.d/conda.sh
#make it permanant
echo 'source ~/miniconda/etc/profile.d/conda.sh' >> ~/.bashrc

# Create and activate conda environment
echo Making petals conda environment
conda create --name petals python=3.10 pip -y
conda activate petals

# install cuda
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/ /"
sudo apt-get update
sudo apt-get -y install cuda
# Add cuda to the path
export PATH=/usr/local/cuda/bin:$PATH
#make it permanant
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
export LD_LIBRARY_PATH=/usr/local/cuda-12.2/targets/x86_64-linux/lib/:$LD_LIBRARY_PATH
#make it permanant
echo "export LD_LIBRARY_PATH=/usr/local/cuda-12.2/targets/x86_64-linux/lib/:$LD_LIBRARY_PATH" >> ~/.bashrc
# Install petals
echo "Installing petals"
pip install --upgrade git+https://github.com/bigscience-workshop/petals
pip install --upgrade pyyaml

echo "Installing PyQt5"
pip install PyQt5
echo "Installing PyQt5 Web engine"
pip install PyQtWebEngine
sudo apt-get install libxcursor1

echo cloning petals-server-installer
cd ~
git clone https://github.com/ParisNeo/petals_server_installer.git
cd ~/petals_server_installer
# Exit WSL
exit
