import sys
import subprocess
import psutil
import yaml  # Import the PyYAML library
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

class ServerInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Server Info App")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Load the list of models from a YAML file
        self.models = self.load_models_from_yaml("models.yaml")

        # Add QComboBox for model selection
        self.model_label = QLabel("Select Model:")
        self.model_combo = QComboBox()
        for model in self.models:
            self.model_combo.addItem(model)
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

    def load_models_from_yaml(self, file_path):
        try:
            with open(file_path, "r") as yaml_file:
                models = yaml.safe_load(yaml_file)
            return models
        except FileNotFoundError:
            return []

    # Rest of the code remains unchanged...

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerInfoApp()
    window.show()
    sys.exit(app.exec_())
