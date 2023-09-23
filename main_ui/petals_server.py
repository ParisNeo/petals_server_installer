import sys
import subprocess
import psutil
import yaml
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit
from PyQt5.QtCore import QProcess

class ServerInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = self.get_config()

        self.setWindowTitle("Server Info App")
        self.setGeometry(100, 100, 600, 500)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Load the list of models from a YAML file
        self.models = self.load_models_from_yaml("models.yaml")

        # Add QComboBox for model selection
        self.model_label = QLabel("Select Model:")
        self.model_combo = QComboBox()
        for model in self.models:
            self.model_combo.addItem(model["name"])
        try:
            self.model_combo.setCurrentIndex(self.config['model_id'])
        except:
            print("Couldn't set model id")
        self.layout.addWidget(self.model_label)
        self.layout.addWidget(self.model_combo)

        self.node_name_label = QLabel("Node Name:")
        self.node_name_entry = QLineEdit()
        self.node_name_entry.setText(self.config['node_name'])
        self.layout.addWidget(self.node_name_label)
        self.layout.addWidget(self.node_name_entry)

        # Detect available GPU devices and add them to the QComboBox
        self.device_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        available_devices = self.detect_gpu_devices()
        self.device_combo.addItem("auto")
        self.device_combo.addItem("cpu")
        self.devices=["auto", "cpu"]
        for i, device in enumerate(available_devices):
            self.device_combo.addItem(device)
            self.devices.append(f"cuda:{i}")
        self.layout.addWidget(self.device_label)
        self.layout.addWidget(self.device_combo)

        # Token entry field
        self.token_label = QLabel("Token (if required):")
        self.token_entry = QLineEdit()
        self.layout.addWidget(self.token_label)
        self.layout.addWidget(self.token_entry)

        self.start_server_button = QPushButton("Start Server")
        self.start_server_button.clicked.connect(self.start_server)
        self.layout.addWidget(self.start_server_button)

        # Display resource usage information
        self.resource_info_label = QLabel("Resource Usage:")
        self.resource_info = QLabel()
        self.layout.addWidget(self.resource_info_label)
        self.layout.addWidget(self.resource_info)

        # QTextEdit widget for displaying server stdout
        self.stdout_label = QLabel("Server Output:")
        self.stdout_text = QTextEdit()
        self.stdout_text.setReadOnly(True)
        self.stdout_text.setLineWrapMode(QTextEdit.NoWrap)
        self.layout.addWidget(self.stdout_label)
        self.layout.addWidget(self.stdout_text)

        self.server_process = None

    def get_config(self):
        # Define the YAML data structure
        config_data = {
            'node_name': 'Unnamed',
            'model_id': 0,
            'token': '',
        }

        # Check if config.yaml exists in the current folder
        config_path = Path(__file__).resolve().parent / 'config.yaml'

        if not config_path.exists():
            # If the file doesn't exist, create it with the specified structure
            with open(config_path, 'w') as config_file:
                yaml.dump(config_data, config_file, default_flow_style=False)
            print("config.yaml file created.")
        else:
            # If the file exists, load its content
            with open(config_path, 'r') as config_file:
                config_data = yaml.load(config_file, Loader=yaml.FullLoader)
                print("Previous config:")
                print(config_data)
        return config_data
            
    def load_models_from_yaml(self, file_path):
        try:
            with open(file_path, "r") as yaml_file:
                models = yaml.safe_load(yaml_file)
            return models
        except FileNotFoundError:
            return []

    def detect_gpu_devices(self):
        try:
            output = subprocess.check_output(["nvidia-smi", "--list-gpus"], universal_newlines=True)
            devices = [line.strip() for line in output.split('\n') if line.strip()]
            return devices
        except subprocess.CalledProcessError:
            return []

    def start_server(self):
        selected_model_name = self.model_combo.currentText()
        selected_model = next((model for model in self.models if model["name"] == selected_model_name), None)

        node_name = self.node_name_entry.text().strip()
        device = self.device_combo.currentText()
        token = self.token_entry.text().strip()

        if not node_name:
            self.resource_info.setText("Node Name is required.")
            return

        command = [
            "python3",
            "-m",
            "petals.cli.run_server",
            selected_model["name"],
            "--public_name",
            node_name,
            "--device",
            device,
        ]

        if selected_model.get("token"):
            command.extend(["--token", token])

        print(f"Command : {command}")
        try:
            # Start the server process and capture its stdout
            self.server_process = QProcess()
            self.server_process.setProcessChannelMode(QProcess.MergedChannels)
            self.server_process.readyReadStandardOutput.connect(self.update_stdout_text)
            self.server_process.start(" ".join(command))
            self.resource_info.setText("Server started successfully!")

            # Update resource usage information
            self.update_resource_info()
        except Exception as e:
            self.resource_info.setText(f"Error starting the server: {str(e)}")

    def update_resource_info(self):
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        gpu_info = subprocess.check_output(["nvidia-smi"], universal_newlines=True)

        resource_text = f"CPU Usage: {cpu_usage}%\n"
        resource_text += f"Memory Usage: {memory_info.percent}%\n"
        resource_text += "GPU Information:\n"
        resource_text += gpu_info

        self.resource_info.setText(resource_text)

    def update_stdout_text(self):
        data = self.server_process.readAll()
        text = data.data().decode("utf-8")
        self.stdout_text.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerInfoApp()
    window.show()
    sys.exit(app.exec_())
