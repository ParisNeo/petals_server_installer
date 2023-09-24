"""
    Petals Server Installer

    Author: ParisNeo
    Version: 1.0.0
    Description: A standalone installer for Petals, a decentralized text generation network.

    This Python script provides the functionality for configuring and testing a Petals server node.
"""
import sys
import subprocess
import psutil
import yaml
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QSplitter,  QSpinBox
from PyQt5.QtGui import QTextCursor, QTextOption, QFont
from PyQt5.QtCore import QProcess, Qt

from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM
from PyQt5.QtCore import QCoreApplication

from PyQt5.QtCore import QThread, pyqtSignal

class PetalsServiceMonitor(QMainWindow):
    """
    Petals Service Monitor

    This PyQt5 application provides a user interface for monitoring Petals service status,
    server hardware details, GPU status, CPU usage, and memory usage in a Windows Subsystem for Linux (WSL) environment.

    """    
    def __init__(self):
        """
        Initialize the Petals Service Monitor UI.

        This method sets up the main window, configures UI elements, and initializes variables for server management.

        - Loads user configuration.
        - Sets up the main window and its appearance.
        - Creates left and right layouts for input widgets and server output.
        - Initializes buttons, labels, and text input fields.
        - Configures UI styles with a global stylesheet.
        - Connects button click events to their respective functions.
        - Sets up a QSplitter to arrange the left and right layouts.

        """        
        super().__init__()

        self.config = self.get_config()
        self.model = None
        self.generation_thread = None

        self.setWindowTitle("Petals Service monitor UI")
        self.setGeometry(100, 100, 800, 500)

        # Apply a global stylesheet for the main window
        main_window_stylesheet = (
            "QMainWindow {"
            "background-color: #5e5757;"
            "}"
            "QPushButton {"
            "background-color: #6e4e15;"
            "border: none;"
            "color: white;"
            "padding: 10px;"
            "border-radius: 5px;"
            "}"
            "QPushButton:hover {"
            "background-color: #d67702;"
            "}"
            "QTextEdit, QLineEdit, QSpinBox {"
            "background-color: #9c9494;"
            "border: none;"
            "padding: 5px;"
            "border-radius: 5px;"
            "}"
            "QComboBox {"
            "background-color: #9c9494;"  # Background color for combo box
            "border: none;"
            "padding: 5px;"
            "border-radius: 5px;"
            "}"
            "QComboBox::drop-down {"
            "subcontrol-origin: padding;"
            "subcontrol-position: top right;"
            "width: 20px;"
            "border-left-width: 1px;"
            "border-left-color: darkgray;"
            "border-left-style: solid;"
            "border-top-right-radius: 5px;"
            "border-bottom-right-radius: 5px;"
            "}"
            "QLabel {"
            "color: white;"
            "}"
        )
        self.setStyleSheet(main_window_stylesheet)        

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
        print(f'using device {self.config["device"]}')
        self.device_combo.setCurrentIndex(self.config["device"])

        # Token entry field
        self.token_label = QLabel("Token (if required):")
        self.token_entry = QLineEdit()
        left_layout.addWidget(self.token_label)
        left_layout.addWidget(self.token_entry)
        # Num Blocks entry field for CPU
        self.num_blocks_label = QLabel("Num Blocks (the number of blocks to serve, -1 for auto):")
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

        left_layout.addLayout(buttons_layout)

        self.link_label = QLineEdit("View Network Health on https://health.petals.dev/")
        left_layout.addWidget(self.link_label)

        self.max_new_tokens_label = QLabel("Max new tokens for inference:")
        # Create a QSpinBox widget
        self.max_new_tokens_input = QSpinBox()
        self.max_new_tokens_input.setMinimum(5)  # Set minimum value
        self.max_new_tokens_input.setMaximum(16384)  # Set maximum value
        self.max_new_tokens_input.setValue(self.config["max_new_tokens"])

        left_layout.addWidget(self.max_new_tokens_label)
        left_layout.addWidget(self.max_new_tokens_input)

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
        self.stdout_label = QLabel("Test client (Please wait till the server is fully loaded):")
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        right_layout.addWidget(self.stdout_label)
        right_layout.addWidget(self.response_text)

        # QLineEdit for user input
        input_layout = QHBoxLayout()
        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText("Enter your prompt...")
        self.input_prompt.returnPressed.connect(self.generate_response)
        self.input_prompt.setEnabled(False)
        input_layout.addWidget(self.input_prompt)        
        # QPushButton to trigger response generation
        self.generate_button = QPushButton("Generate Response")
        self.generate_button.clicked.connect(self.generate_response)
        input_layout.addWidget(self.generate_button)
        self.generate_button.setEnabled(False)
        right_layout.addLayout(input_layout)

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
        """
        Load or create the configuration data for the Petals Service Monitor.

        This method checks if the 'config.yaml' file exists in the current folder. If it does not exist, it creates a
        default configuration file. If it exists, it loads the configuration from the file and returns it.

        Returns:
            dict: The configuration data loaded from the 'config.yaml' file or the default configuration data.

        """        
        # Define the YAML data structure
        config_data = {
            'node_name': 'Unnamed',
            'device': 0,
            'model_id': 0,
            'token': '',
            'num_blocks': 4,
            'generation_template':"{system_prompt}### User: {message}\n\n### Assistant:\n",
            "system_prompt":"Act as an AI assistant that is always ready to provide useful information and assistance. Help the user acheive his task.",
            'max_new_tokens':1024
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

    def update_config_from_ui(self):
        """
        Update the 'config' dictionary with values from the UI components.

        This method retrieves the configuration settings from the UI components and updates the 'config'
        dictionary with these values.

        """
        # Get the selected model name and index
        selected_model_name = self.model_combo.currentText()
        selected_model_index = self.model_combo.currentIndex()

        # Get the node name, device ID, token, num_blocks, and max_new_tokens from UI components
        node_name = self.node_name_entry.text().strip()
        device_id = self.device_combo.currentIndex()
        token = self.token_entry.text().strip()
        num_blocks = self.num_blocks_entry.text().strip()
        max_new_tokens = self.max_new_tokens_input.value()

        # Update the 'config' dictionary with the new values
        self.config.update({
            'node_name': node_name,
            'device': device_id,
            'model_id': selected_model_index,
            'token': token,
            'num_blocks': num_blocks,
            'max_new_tokens': max_new_tokens
        })

    def save_config(self):
        """
        Save the current configuration settings to the 'config.yaml' file.

        This method updates the 'config' dictionary with values from the UI components using the
        'update_config_from_ui' method. It then writes the 'config' dictionary to the 'config.yaml' file
        to save the configuration.

        """        
        # Update the 'config' dictionary from the UI
        self.update_config_from_ui()

        # Define the path to the 'config.yaml' file
        config_path = Path(__file__).resolve().parent / 'config.yaml'

        # Write the 'config' dictionary to the 'config.yaml' file
        with open(config_path, 'w') as config_file:
            yaml.dump(self.config, config_file, default_flow_style=False)        

        print("Configuration saved")


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
            self.model = None
            self.input_prompt.setEnabled(False)
            self.generate_button.setEnabled(False)
            self.server_process.terminate()
            self.start_server_button.setText("Start Server")
        else:
            self.save_config()            
            selected_model_name = self.model_combo.currentText()
            selected_model = next((model for model in self.models if model["name"] == selected_model_name), None)

            node_name = self.node_name_entry.text().strip()
            device_id = self.device_combo.currentIndex()
            device = self.devices[device_id]
            token = self.token_entry.text().strip()
            num_blocks = self.num_blocks_entry.text().strip()

            if not node_name:
                self.resource_info.setText("Node Name is required.")
                return

            # Choose any model available at https://health.petals.dev
            self.model_name = selected_model_name

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

            if num_blocks!='-1':
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
            self.generate_button.setEnabled(True)
            self.input_prompt.setEnabled(True)
            QCoreApplication.processEvents()

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
        self.generate_button.setEnabled(False)
        self.input_prompt.setEnabled(False)

        if self.model is None:
            self.generate_button.setText("Loading ...")
            QCoreApplication.processEvents()
            selected_model_name = self.model_combo.currentText()
            selected_model = next((model for model in self.models if model["name"] == selected_model_name), None)
            # Connect to a distributed network hosting model layers
            self.tokenizer = AutoTokenizer.from_pretrained(selected_model["name"])
            self.model = AutoDistributedModelForCausalLM.from_pretrained(selected_model["name"])

        self.generate_button.setText("Generating...")
        QCoreApplication.processEvents()
        user_prompt = self.input_prompt.text()
        if user_prompt:
            # Replace placeholders in the template
            formatted_message = self.config["generation_template"].format(system_prompt=self.config["system_prompt"], message=user_prompt)

            # Create and start the generation thread
            self.generation_thread = GenerationThread(self.model, self.tokenizer, user_prompt, formatted_message, self.config["max_new_tokens"])
            self.generation_thread.finished.connect(self.handle_generation_finished)
            self.generation_thread.start()
        else:
            self.response_text.setPlainText("Please enter a prompt.")

    def handle_generation_finished(self, generated_text):
        self.response_text.setPlainText(generated_text)
        self.generate_button.setText("Generate Response")
        self.generate_button.setEnabled(True)
        self.input_prompt.setEnabled(True)
        QCoreApplication.processEvents()

class GenerationThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, tokenizer, user_prompt, formatted_message, max_new_tokens):
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.user_prompt = user_prompt
        self.formatted_message = formatted_message
        self.max_new_tokens = max_new_tokens

    def run(self):
        # Generate response in a background thread
        inputs = self.tokenizer(self.formatted_message, return_tensors="pt")["input_ids"]
        outputs = self.model.generate(inputs, max_new_tokens=self.max_new_tokens)
        generated_text = self.tokenizer.decode(outputs[0])
        generated_text = generated_text.replace("<s> ", "").replace("</s>", "")[len(self.formatted_message):]
        self.finished.emit(generated_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PetalsServiceMonitor()
    window.showMaximized()
    sys.exit(app.exec_())
