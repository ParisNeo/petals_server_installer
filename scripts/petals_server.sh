#!/bin/bash
# activate conda environment
echo sourcing miniconda
source ~/miniconda/etc/profile.d/conda.sh
echo activating environment
conda activate petals
echo running server ui
# Run the Python command with the chosen model name
cd ~/petals_server_installer/main_ui
python3 petals_server.py
