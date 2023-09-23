import sys
import subprocess
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

class ServerInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Server Info App")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Add QComboBox for model selection
        self.model_label = QLabel("Select Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItem("Model 1")
        self.model_combo.addItem("Model 2")
        self.layout.addWidget(self.model_label)
        self.layout.addWidget(self.model_combo)

        self.node_name_label = QLabel("Node Name:")
        self.node_name_entry = QLineEdit()
        self.layout.addWidget(self.node_name_label)
        self.layout.addWidget(self.node_name_entry)

        # Detect available GPU devices and add them to the QComboBox
        self.device_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        available_devices = self.detect_gpu_devices()
        for device in available_devices:
            self.device_combo.addItem(device)
        self.layout.addWidget(self.device_label)
        self.layout.addWidget(self.device_combo)

        self.start_server_button = QPushButton("Start Server")
        self.start_server_button.clicked.connect(self.start_server)
        self.layout.addWidget(self.start_server_button)

        # Display resource usage information
        self.resource_info_label = QLabel("Resource Usage:")
        self.resource_info = QLabel()
        self.layout.addWidget(self.resource_info_label)
        self.layout.addWidget(self.resource_info)

    def detect_gpu_devices(self):
        try:
            output = subprocess.check_output(["nvidia-smi", "--list-gpus"], universal_newlines=True)
            devices = [line.strip() for line in output.split('\n') if line.strip()]
            return devices
        except subprocess.CalledProcessError:
            return []

    def start_server(self):
        model_name = self.model_combo.currentText()
        node_name = self.node_name_entry.text().strip()
        device = self.device_combo.currentText()

        if not node_name:
            self.resource_info.setText("Node Name is required.")
            return

        command = [
            "python3",
            "-m",
            "petals.cli.run_server",
            model_name,
            "--public_name",
            node_name,
            "--device",
            device,
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.resource_info.setText("Server started successfully!")

            # Update resource usage information
            self.update_resource_info()
        except subprocess.CalledProcessError as e:
            self.resource_info.setText(f"Error starting the server: {e.stderr.decode('utf-8')}")

    def update_resource_info(self):
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        gpu_info = subprocess.check_output(["nvidia-smi"], universal_newlines=True)

        resource_text = f"CPU Usage: {cpu_usage}%\n"
        resource_text += f"Memory Usage: {memory_info.percent}%\n"
        resource_text += "GPU Information:\n"
        resource_text += gpu_info

        self.resource_info.setText(resource_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerInfoApp()
    window.show()
    sys.exit(app.exec_())
