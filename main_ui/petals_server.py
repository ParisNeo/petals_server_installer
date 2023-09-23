import sys
import subprocess
import psutil
import yaml
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QSplitter
from PyQt5.QtGui import QTextCursor, QTextOption, QFont
from PyQt5.QtCore import QProcess, Qt

from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM
from PyQt5.QtCore import QCoreApplication

class PetalsServiceMonitor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = self.get_config()

        self.setWindowTitle("Petals Service monitor UI")
        self.setGeometry(100, 100, 800, 500)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        # Left side layout for input widgets
        left_layout = QVBoxLayout()

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
        left_layout.addWidget(self.model_label)
        left_layout.addWidget(self.model_combo)

        self.node_name_label = QLabel("Node Name:")
        self.node_name_entry = QLineEdit()
        self.node_name_entry.setText(self.config['node_name'])
        left_layout.addWidget(self.node_name_label)
        left_layout.addWidget(self.node_name_entry)

        # Detect available GPU devices and add them to the QComboBox
        self.device_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        available_devices = self.detect_gpu_devices()
        self.device_combo.addItem("cpu")
        self.devices=["cpu"]
        for i, device in enumerate(available_devices):
            self.device_combo.addItem(device)
            self.devices.append(f"cuda:{i}")
        left_layout.addWidget(self.device_label)
        left_layout.addWidget(self.device_combo)

        # Token entry field
        self.token_label = QLabel("Token (if required):")
        self.token_entry = QLineEdit()
        left_layout.addWidget(self.token_label)
        left_layout.addWidget(self.token_entry)
        # Num Blocks entry field for CPU
        self.num_blocks_label = QLabel("Num Blocks (for CPU):")
        self.num_blocks_entry = QLineEdit()
        self.num_blocks_entry.setText(str(self.config['num_blocks']))
        left_layout.addWidget(self.num_blocks_label)
        left_layout.addWidget(self.num_blocks_entry)
        
        # Add an "Update Usage" button

        buttons_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save config")
        self.save_config_button.clicked.connect(self.save_config)
        buttons_layout.addWidget(self.save_config_button)   

        self.update_usage_button = QPushButton("Update Usage")
        self.update_usage_button.clicked.connect(self.update_resource_info)
        buttons_layout.addWidget(self.update_usage_button)        

        self.start_server_button = QPushButton("Start Server")
        self.start_server_button.clicked.connect(self.start_server)
        buttons_layout.addWidget(self.start_server_button)

        left_layout.addWidget(buttons_layout)

        self.link_label = QLabel("<a href='https://health.petals.dev/'>View Network Health on https://health.petals.dev/</a>")
        self.link_label.setTextFormat(Qt.RichText)
        self.link_label.setOpenExternalLinks(True)
        left_layout.addWidget(self.link_label)

        self.resource_info_label = QLabel("Resource Usage:")
        self.resource_info = QTextEdit()
        self.resource_info.setReadOnly(True)
        # Set a monospaced font for the QTextEdit
        monospaced_font = QFont("Courier New", 10)  # Adjust the font and size as needed
        self.resource_info.setFont(monospaced_font)
        # Disable text wrapping
        self.resource_info.setLineWrapMode(QTextEdit.NoWrap)
        # Enable horizontal scrollbar as needed
        self.resource_info.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resource_info.setWordWrapMode(QTextOption.NoWrap)

        left_layout.addWidget(self.resource_info_label)
        left_layout.addWidget(self.resource_info)

        # Right side layout for server output
        right_layout = QVBoxLayout()

        self.stdout_label = QLabel("Server Output:")
        self.stdout_text = QTextEdit()
        self.stdout_text.setReadOnly(True)
        monospaced_font = QFont("Courier New", 10)  # Adjust the font and size as needed
        self.stdout_text.setFont(monospaced_font)
        # Disable text wrapping
        self.stdout_text.setLineWrapMode(QTextEdit.NoWrap)
        # Enable horizontal scrollbar as needed
        self.stdout_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stdout_text.setWordWrapMode(QTextOption.NoWrap)

        right_layout.addWidget(self.stdout_label)
        right_layout.addWidget(self.stdout_text)

        # QTextEdit for displaying model responses
        self.stdout_label = QLabel("Test client:")
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        right_layout.addWidget(self.response_text)

        # QLineEdit for user input
        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText("Enter your prompt...")
        right_layout.addWidget(self.input_prompt)        
        # QPushButton to trigger response generation
        self.generate_button = QPushButton("Generate Response")
        self.generate_button.clicked.connect(self.generate_response)
        right_layout.addWidget(self.generate_button)
        self.generate_button.setEnabled(False)

        # Use a QSplitter to arrange the left and right layouts
        splitter = QSplitter()
        splitter.addWidget(QWidget())
        splitter.addWidget(QWidget())
        splitter.setSizes([self.width() // 3, self.width() * 2 // 3])
        splitter.setStyleSheet("QSplitter::handle { background-color: lightgray; }")
        splitter.setContentsMargins(0, 0, 0, 0)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.widget(0).setLayout(left_layout)
        splitter.widget(1).setLayout(right_layout)

        self.layout.addWidget(splitter)

        self.server_process = None

    def get_config(self):
        # Define the YAML data structure
        config_data = {
            'node_name': 'Unnamed',
            'device': 0,
            'model_id': 0,
            'token': '',
            'num_blocks': 4,
            'generation_template':"{system_prompt}### User: {message}\n\n### Assistant:\n",
            "system_prompt":"Act as an AI assistant that is always ready to provide useful information and assistance. Help the user acheive his task."
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
    
    def save_config(self):
        selected_model_name = self.model_combo.currentText()
        selected_model_index = self.model_combo.currentIndex()

        node_name = self.node_name_entry.text().strip()
        device_id = self.device_combo.currentIndex()
        token = self.token_entry.text().strip()
        num_blocks = self.num_blocks_entry.text().strip()

        config_data = {
            'node_name': node_name,
            'device': device_id,
            'model_id': selected_model_index,
            'token': token,
            'num_blocks': num_blocks,
            'generation_template':self.config["generation_template"],
            "system_prompt":self.config["system_prompt"]                
        }
        config_path = Path(__file__).resolve().parent / 'config.yaml'
        with open(config_path, 'w') as config_file:
            yaml.dump(config_data, config_file, default_flow_style=False)        

        self.config = config_data


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
        if self.start_server_button.text()=="Stop Server":
            self.server_process.terminate()
            self.start_server_button.setText("Start Server")
        else:
            selected_model_name = self.model_combo.currentText()
            selected_model_index = self.model_combo.currentIndex()
            selected_model = next((model for model in self.models if model["name"] == selected_model_name), None)

            node_name = self.node_name_entry.text().strip()
            device_id = self.device_combo.currentIndex()
            device = self.devices[device_id]
            token = self.token_entry.text().strip()
            num_blocks = self.num_blocks_entry.text().strip()

            config_data = {
                'node_name': node_name,
                'device': device_id,
                'model_id': selected_model_index,
                'token': token,
                'num_blocks': num_blocks,
                'generation_template':self.config["generation_template"],
                "system_prompt":self.config["system_prompt"]                
            }
            config_path = Path(__file__).resolve().parent / 'config.yaml'
            with open(config_path, 'w') as config_file:
                yaml.dump(config_data, config_file, default_flow_style=False)
            print("config.yaml file created.")
            self.config = config_data

            if not node_name:
                self.resource_info.setText("Node Name is required.")
                return

            # Choose any model available at https://health.petals.dev
            self.model_name = "petals-team/StableBeluga2"  # This one is fine-tuned Llama 2 (70B)

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

            if device=="cpu":
                command.extend(["--num_blocks", num_blocks])

            print(f"Command : {command}")
            try:
                # Start the server process and capture its stdout
                self.server_process = QProcess()
                self.server_process.setProcessChannelMode(QProcess.MergedChannels)
                self.server_process.readyReadStandardOutput.connect(self.update_stdout_text)
                self.server_process.start(" ".join(command))
                self.resource_info.setText("Server started successfully!")
                self.start_server_button.setText("Stop Server")

                # Update resource usage information
                self.update_resource_info()
            except Exception as e:
                self.resource_info.setText(f"Error starting the server: {str(e)}")
            
            # Force the application to execute the event loop
            QCoreApplication.processEvents()
            # Connect to a distributed network hosting model layers
            self.tokenizer = AutoTokenizer.from_pretrained(selected_model["name"])
            self.model = AutoDistributedModelForCausalLM.from_pretrained(selected_model["name"])
            self.generate_button.setEnabled(True)

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
        
        # Check if the text contains carriage return characters
        if '\r' in text:
            # Split the text by carriage returns
            lines = text.split('\r')
            
            # Take the last line to update the existing line
            last_line = lines[-1]
            
            # Update the last line in the QTextEdit
            cursor = self.stdout_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertText(last_line)
        else:
            # If no carriage return characters are found, simply append the text
            self.stdout_text.append(text)

    # Create a function to generate and display responses
    def generate_response(self):
        user_prompt = self.input_prompt.text()
        if user_prompt:
            # Replace placeholders in the template
            formatted_message = self.config["generation_template"].format(system_prompt=self.config["system_prompt"] , message=user_prompt)

            # Run the model as if it were on your computer
            inputs = self.tokenizer(formatted_message, return_tensors="pt")["input_ids"]
            outputs = self.model.generate(inputs, max_new_tokens=5)
            generated_text = self.tokenizer.decode(outputs[0])
            self.response_text.setPlainText(generated_text)
        else:
            self.response_text.setPlainText("Please enter a prompt.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PetalsServiceMonitor()
    window.show()
    sys.exit(app.exec_())
