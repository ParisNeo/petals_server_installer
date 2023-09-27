# Petals Network Installer and Server Info App

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
![GitHub stars](https://img.shields.io/github/stars/ParisNeo/petals_server_installer.svg?style=social)
![GitHub issues](https://img.shields.io/github/issues/ParisNeo/petals_server_installer.svg)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ParisNeo/petals_server_installer/CI)
![GitHub license](https://img.shields.io/github/license/ParisNeo/petals_server_installer.svg)
![GitHub contributors](https://img.shields.io/github/contributors/ParisNeo/petals_server_installer.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/ParisNeo/petals_server_installer.svg)

Petals Server Installer is a standalone installer for Petals, a decentralized text generation network. This tool simplifies the installation of a Petals server on various platforms. You can use it to set up a Petals server on Windows using Windows Subsystem for Linux (WSL) via the `petals-server.exe` or on Linux/macOS using the `install_script.sh`.

## Features

- Easily configure and install a Petals server.
- User-friendly graphical user interface (GUI) for server setup and inference testing.
- Launch an Ubuntu environment for debugging or development on Windows.
- Manage your Petals server settings through the `config.yaml` file.

## Installation

### Windows

From release page, download `petals-server.exe` and install it.

After installation, you will have two new shortcuts:

1. **Load Ubuntu**: Opens an Ubuntu environment for debugging or development.
2. **Load Petals Server UI**: Launches the Petals Server UI.

### Linux/macOS

From release page, download `install_script.sh` and run it with bash.

1. The installer creates a Conda environment named "petals" for you.
2. Activate the environment with `conda activate petals`.
3. Navigate to `~/petals_server_installer/main_ui/`.
4. Start the Petals Server UI with `python3 petals_server.py`.

## Configuration

The `config.yaml` file, located at `~/petals_server_installer/main_ui/`, stores various configurations. Most settings can be conveniently modified through the UI. However, you can manually adjust the `prompt` and `conditioning_format` settings.

### Manual Configuration (Linux/macOS)

To modify the `config.yaml` file manually on Linux/macOS:

1. Activate the Conda environment: `conda activate petals`.
2. Navigate to the `main_ui` folder: `cd ~/petals_server_installer/main_ui/`.
3. Use a text editor like `nano` to view and modify `config.yaml`.

We hope you find Petals Server Installer helpful for setting up and managing your Petals server. Enjoy seamless text generation with Petals!

## Star History

<a href="https://star-history.com/#ParisNeo/petals_server_installer&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=ParisNeo/petals_server_installer&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=ParisNeo/petals_server_installer&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=ParisNeo/petals_server_installer&type=Date" />
  </picture>
</a>


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
