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
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QSplitter,  QSpinBox, QTabWidget, QGroupBox, QTextBrowser
from PyQt5.QtGui import QTextCursor, QTextOption, QFont
from PyQt5.QtCore import QProcess, Qt


from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM
from PyQt5.QtCore import QCoreApplication

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

import torch

# The data types that can be used for inference 
dtypes = [
    torch.float16,
    torch.float32
    ]
str_dtypes = [
    "float16",
    "float32"
]


class GenerationThread(QThread):
    """
    A PyQt QThread class for background text generation.

    This class inherits from QThread and is designed to run text generation in the background. It takes a pre-trained
    model, a tokenizer, user input prompt, a formatted message, and a maximum number of new tokens to generate.

    Attributes:
        finished (pyqtSignal): A PyQt signal emitted when text generation is completed, carrying the generated text.

    """

    finished = pyqtSignal(str)

    def __init__(self, model, tokenizer, user_prompt, formatted_message, max_new_tokens):
        """
        Initialize a GenerationThread instance.

        Args:
            model: The pre-trained language model for text generation.
            tokenizer: The tokenizer for tokenizing input text.
            user_prompt (str): The user's input prompt for text generation.
            formatted_message (str): The formatted message that includes system and user prompts.
            max_new_tokens (int): The maximum number of new tokens to generate.

        """
        super().__init__()
        self.model = model
        self.tokenizer = tokenizer
        self.user_prompt = user_prompt
        self.formatted_message = formatted_message
        self.max_new_tokens = max_new_tokens

    def run(self):
        """
        Execute the text generation process in a background thread.

        This method performs the text generation process using the provided model, tokenizer, user input, formatted
        message, and maximum number of tokens. It emits the 'finished' signal with the generated text when the
        generation is completed.

        """
        # Generate response in a background thread
        inputs = self.tokenizer(self.formatted_message, return_tensors="pt")["input_ids"]
        outputs = self.model.generate(inputs, max_new_tokens=self.max_new_tokens)
        generated_text = self.tokenizer.decode(outputs[0])
        generated_text = generated_text.replace("<s> ", "").replace("</s>", "")[len(self.formatted_message):]
        self.finished.emit(generated_text)


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

        # Load configuration
        self.config = self.get_config()

        # Load the list of models from a YAML file
        self.models = self.load_models_from_yaml("models.yaml")

        # Initialize model to None for inference
        self.model = None

        # No generation thread yet
        self.generation_thread = None

        self.setWindowTitle("Petals Service monitor UI")
        self.setGeometry(100, 100, 800, 500)

        # Apply a global stylesheet for the main window
        main_window_stylesheet = (
            "QMainWindow {"
            "background-color: #5e5757;"
            "}"
            "QGroupBox {"
            "    border: 2px solid white;"
            "   border-radius: 5px;"
            "   margin-top: 10px;"
            "}"
            "QGroupBox::title {"
            "    color: white;"
            "}"
            "QWidget { background-color: #333; }"
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
            "QTabWidget::pane { background-color: #333; }"
            "QTabBar::tab { background-color: #555; color: white; }"
            "QTabBar::tab:selected { background-color: #777; }"
            "QTabWidget::pane { background-color: #333; }"
            "QTabBar::tab { background-color: #555; color: white; }"
            "QTabBar::tab:selected { background-color: #777; }"

        )
        self.setStyleSheet(main_window_stylesheet)        

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        # Create a QTabWidget to organize the interface into tabs
        self.tab_widget = QTabWidget()

        # Create tabs and add them to the tab widget
        self.create_server_output_tab()
        self.create_web_browser_tab()
        self.create_settings_tab()
        self.create_resources_tab()
        self.create_text_generation_tab()
        self.create_about_tab()

        # Add the tab widget to the layout
        self.layout.addWidget(self.tab_widget)

    def create_settings_tab(self):
        settings_widget = QWidget()
        settings_up_layout = QHBoxLayout()
        settings_layout = QHBoxLayout()
        settings_up_layout.addLayout(settings_layout)

        # Server Settings
        server_settings_group = QGroupBox("Server Settings")
        server_settings_layout = QVBoxLayout()

        self.model_label = QLabel("Select Model:")
        self.model_combo = QComboBox()
        for model in self.models:
            self.model_combo.addItem(model["name"])
        try:
            self.model_combo.setCurrentIndex(self.config['model_id'])
        except:
            print("Couldn't set model id")
        server_settings_layout.addWidget(self.model_label)
        server_settings_layout.addWidget(self.model_combo)

        self.node_name_label = QLabel("Node Name:")
        self.node_name_entry = QLineEdit()
        self.node_name_entry.setText(self.config['node_name'])
        server_settings_layout.addWidget(self.node_name_label)
        server_settings_layout.addWidget(self.node_name_entry)

        # Detect available GPU devices and add them to the QComboBox
        self.device_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        available_devices = self.detect_gpu_devices()
        self.device_combo.addItem("cpu")
        self.devices=["cpu"]
        for i, device in enumerate(available_devices):
            self.device_combo.addItem(device)
            self.devices.append(f"cuda:{i}")
        server_settings_layout.addWidget(self.device_label)
        server_settings_layout.addWidget(self.device_combo)
        print(f'using device {self.config["device"]}')
        self.device_combo.setCurrentIndex(self.config["device"])

        self.token_label = QLabel("Token (if required):")
        self.token_entry = QLineEdit()
        server_settings_layout.addWidget(self.token_label)
        server_settings_layout.addWidget(self.token_entry)

        self.num_blocks_label = QLabel("Num Blocks (the number of blocks to serve, -1 for auto):")
        self.num_blocks_entry = QLineEdit()
        self.num_blocks_entry.setText(str(self.config['num_blocks']))
        server_settings_layout.addWidget(self.num_blocks_label)
        server_settings_layout.addWidget(self.num_blocks_entry)

        server_settings_group.setLayout(server_settings_layout)
        
        # Inference Settings
        inference_settings_group = QGroupBox("Inference Settings")
        inference_settings_layout = QVBoxLayout()
        self.text_gen_template_label = QLabel("Text generation template")
        self.text_gen_template_text = QTextEdit(self.config["generation_template"])
        inference_settings_layout.addWidget(self.text_gen_template_label)
        inference_settings_layout.addWidget(self.text_gen_template_text)

        self.text_gen_system_prompt_label = QLabel("System Prompt")
        self.text_gen_system_prompt_text = QTextEdit(self.config["system_prompt"])
        inference_settings_layout.addWidget(self.text_gen_system_prompt_label)
        inference_settings_layout.addWidget(self.text_gen_system_prompt_text)

        self.max_new_tokens_label = QLabel("Max new tokens for inference:")
        self.max_new_tokens_input = QSpinBox()
        self.max_new_tokens_input.setMinimum(5)  # Set minimum value
        self.max_new_tokens_input.setMaximum(16384)  # Set maximum value
        self.max_new_tokens_input.setValue(self.config["max_new_tokens"])
        inference_settings_layout.addWidget(self.max_new_tokens_label)
        inference_settings_layout.addWidget(self.max_new_tokens_input)

        self.inference_label = QLabel("Inference data type:")
        self.inference_combo = QComboBox()
        for dtype_ in str_dtypes:
            self.inference_combo.addItem(dtype_)
        try:
            self.inference_combo.setCurrentIndex(self.config['inference_dtype_id'])
        except:
            print("Couldn't set inference id")
        inference_settings_layout.addWidget(self.inference_label)
        inference_settings_layout.addWidget(self.inference_combo)

        inference_settings_group.setLayout(inference_settings_layout)
        
        # Save Config Button
        self.save_config_button = QPushButton("Save config")
        self.save_config_button.clicked.connect(self.save_config)

        settings_layout.addWidget(server_settings_group)
        settings_layout.addWidget(inference_settings_group)
        settings_up_layout.addWidget(self.save_config_button)
        
        settings_widget.setLayout(settings_up_layout)
        self.tab_widget.addTab(settings_widget, "Settings")



    def create_server_output_tab(self):
        """
        Create a tab for displaying server output.

        This method initializes and sets up a tab for displaying server output, which includes any messages or logs
        generated by the server during its operation. It creates the necessary widgets, connects signals and slots
        for updating the server output, and adds them to the tab layout.

        """        
        server_output_widget = QWidget()
        server_output_layout = QVBoxLayout()

        self.start_server_button = QPushButton("Start Server")
        self.start_server_button.clicked.connect(self.start_server)
        server_output_layout.addWidget(self.start_server_button)

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

        server_output_layout.addWidget(self.stdout_label)
        server_output_layout.addWidget(self.stdout_text)

        server_output_widget.setLayout(server_output_layout)
        self.tab_widget.addTab(server_output_widget, "Server Output")

    def create_web_browser_tab(self):
        web_browser_widget = QWidget()
        web_browser_layout = QVBoxLayout()

        # Create a QWebEngineView widget for web content
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)

        # Load the health page
        self.web_view.setUrl(QUrl("https://health.petals.dev"))

        # Create a refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_web_page)

        web_browser_layout.addWidget(self.web_view)
        web_browser_layout.addWidget(refresh_button)

        web_browser_widget.setLayout(web_browser_layout)
        self.tab_widget.addTab(web_browser_widget, "Network health")

    def refresh_web_page(self):
        # Refresh the web page displayed in the QWebEngineView
        self.web_view.reload()


    def create_resources_tab(self):
        """
        Create a tab for displaying resource usage information.

        This method initializes and sets up a tab for displaying resource usage information, including CPU and memory
        usage, GPU information, and any other relevant resource statistics. It creates necessary widgets, connects
        signals and slots for updating resource information, and adds them to the tab layout.

        """        
        resources_widget = QWidget()
        resources_layout = QVBoxLayout()

        self.update_usage_button = QPushButton("Update Usage")
        self.update_usage_button.clicked.connect(self.update_resource_info)
        resources_layout.addWidget(self.update_usage_button)        

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

        resources_layout.addWidget(self.resource_info_label)
        resources_layout.addWidget(self.resource_info)

        resources_widget.setLayout(resources_layout)
        self.tab_widget.addTab(resources_widget, "Resources")

    def create_text_generation_tab(self):
        """
        Create a tab for text generation user interface.

        This method initializes and sets up a tab for text generation, including user input, response display,
        and generation button functionality. It creates necessary widgets, connects signals and slots, and
        adds them to the tab layout.

        """        
        text_generation_widget = QWidget()
        text_generation_layout = QVBoxLayout()

        # QTextEdit for displaying model responses
        self.stdout_label = QLabel("Test client (Please wait till the server is fully loaded):")
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        text_generation_layout.addWidget(self.stdout_label)
        text_generation_layout.addWidget(self.response_text)

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
        text_generation_layout.addLayout(input_layout)

        text_generation_widget.setLayout(text_generation_layout)
        self.tab_widget.addTab(text_generation_widget, "Text Generation")


        self.server_process = None


    def create_about_tab(self):
        about_widget = QWidget()
        about_layout = QVBoxLayout()

        # Create a QTextBrowser widget for rich text display
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)  # Enable opening links in a web browser

        # Define CSS styles for better formatting
        css_style = """
        body {
            font-family: Arial, sans-serif;
        }
        h1 {
            font-size: 24px;
            color: #007bff;
        }
        h2 {
            font-size: 20px;
            color: #333;
        }
        p {
            font-size: 16px;
            color: #666;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        """

        # Set the CSS style
        about_text.setStyleSheet(css_style)

        # Set the rich text content with information about Petals Service Monitor
        about_text.setHtml(
            """
            <html>
            <head/>
            <body>
            <h1>Petals Service Monitor</h1>
            <p>Welcome to the Petals Service Monitor, a versatile application for managing and interacting with machine learning models in a decentralized fashion on the petals peer to peer network.</p>
            
            <h2>Features:</h2>
            <ul>
                <li>Model Selection: Choose from a variety of pre-trained machine learning models.</li>
                <li>Server Configuration: Configure server settings, including node name, device selection, and authentication tokens.</li>
                <li>Resource Monitoring: Keep an eye on CPU, memory, and GPU usage in real-time.</li>
                <li>Text Generation: Generate responses from selected models based on user input.</li>
                <li>Network health monitoring: View network health page and update it to have a better view of the different models and the number of nodes serving them.</li>
                <li>GitHub Repository: Get the latest updates and contribute to the project on our <a href="https://github.com/ParisNeo/petals_server_installer">GitHub repository</a>.</li>
            </ul>

            <h2>About the Author:</h2>
            <p>Petals Service Monitor was created by ParisNeo, an enthusiastic developer passionate about machine learning integration.</p>
            <p>ParisNeo is also known for the <a href="https://github.com/ParisNeo/lollms-webui">Lord Of Large Language Models project (lollms for short)</a>.</p>

            <h2>GitHub Repository:</h2>
            <p>For more information, updates, and contributions, please visit the <a href="https://github.com/ParisNeo/petals_server_installer">GitHub repository</a> of this application.</p>
            </body>
            </html>
            """
        )

        about_layout.addWidget(about_text)
        about_widget.setLayout(about_layout)
        self.tab_widget.addTab(about_widget, "About Petals Service Monitor")



    def get_config(self):
        """
        Load or create the configuration data for the Petals Service Monitor.

        This method checks if the 'config.yaml' file exists in the current folder. If it does not exist, it creates a
        default configuration file. If it exists, it loads the configuration from the file and returns it. Any missing keys
        in the loaded configuration will be set to their default values for retro compatibility.

        Returns:
            dict: The configuration data loaded from the 'config.yaml' file or the default configuration data.

        """
        # Define the YAML data structure with default values
        default_config_data = {
            'node_name': 'Unnamed',
            'device': 0,
            'model_id': 0,
            'token': '',
            'num_blocks': 4,
            'inference_dtype_id': 0,
            'generation_template': "{system_prompt}### User: {message}\n\n### Assistant:\n",
            "system_prompt": "Act as an AI assistant that is always ready to provide useful information and assistance. Help the user acheive his task.",
            'max_new_tokens': 1024
        }

        # Check if config.yaml exists in the current folder
        config_path = Path(__file__).resolve().parent / 'config.yaml'

        if not config_path.exists():
            # If the file doesn't exist, create it with the default structure
            with open(config_path, 'w') as config_file:
                yaml.dump(default_config_data, config_file, default_flow_style=False)
            print("config.yaml file created.")

        # Load the configuration from the file
        with open(config_path, 'r') as config_file:
            loaded_config_data = yaml.load(config_file, Loader=yaml.FullLoader)
            print("Loaded config:")
            print(loaded_config_data)

        # Update any missing keys in the loaded configuration with default values
        config_data = {**default_config_data, **loaded_config_data}

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

        inference_dtype_id = self.inference_combo.currentIndex()

        generation_template = self.text_gen_template_text.plainText().strip()
        system_prompt = self.text_gen_system_prompt_text.plainText().strip()


        # Update the 'config' dictionary with the new values
        self.config.update({
            'node_name': node_name,
            'device': device_id,
            'model_id': selected_model_index,
            'token': token,
            'num_blocks': num_blocks,
            'inference_dtype_id': inference_dtype_id,
            'max_new_tokens': max_new_tokens,
            'generation_template':generation_template,
            'system_prompt':system_prompt
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
        """
        Load models from a YAML file.

        Args:
            file_path (str): The path to the YAML file containing model data.

        Returns:
            list: A list of dictionaries representing models.
        """
        try:
            with open(file_path, "r") as yaml_file:
                models = yaml.safe_load(yaml_file)
            return models
        except FileNotFoundError:
            return []

    def detect_gpu_devices(self):
        """
        Detect available GPU devices.

        Returns:
            list: A list of GPU device names.
        """
        try:
            output = subprocess.check_output(["nvidia-smi", "--list-gpus"], universal_newlines=True)
            devices = [line.strip() for line in output.split('\n') if line.strip()]
            return devices
        except subprocess.CalledProcessError:
            return []

    def start_server(self):
        """
        Start or stop the Petals server.

        If the server is running, this method stops it. If the server is not running, it starts the server with the
        specified configuration.

        This method reads the configuration from the UI components and constructs the command to start the server. It
        also updates resource information and handles server termination.

        """
        if self.start_server_button.text() == "Stop Server":
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

            if num_blocks != '-1':
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
        """
        Update and display resource usage information.

        This method retrieves and displays information about CPU usage, memory usage, and GPU information (if available).
        It updates the `resource_info` QTextEdit widget with the collected information.

        """
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        gpu_info = subprocess.check_output(["nvidia-smi"], universal_newlines=True)

        resource_text = f"CPU Usage: {cpu_usage}%\n"
        resource_text += f"Memory Usage: {memory_info.percent}%\n"
        resource_text += "GPU Information:\n"
        resource_text += gpu_info

        self.resource_info.setText(resource_text)

    def update_stdout_text(self):
        """
        Update the standard output text in real-time.

        This method is connected to the standard output of the server process. It reads the output data in real-time
        and appends it to the `stdout_text` QTextEdit widget. It also handles carriage return characters to provide a
        smooth and responsive display.

        """
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
        """
        Generate and display responses based on user input.

        This method handles the process of generating responses using the configured model. It retrieves user input,
        formats it according to the specified template, and initiates the response generation process. The generated
        response is then displayed in the `response_text` QTextEdit widget.

        """
        self.generate_button.setEnabled(False)
        self.input_prompt.setEnabled(False)

        if self.model is None:
            self.generate_button.setText("Loading ...")
            QCoreApplication.processEvents()
            selected_model_name = self.model_combo.currentText()
            selected_model = next((model for model in self.models if model["name"] == selected_model_name), None)
            # Connect to a distributed network hosting model layers
            self.tokenizer = AutoTokenizer.from_pretrained(selected_model["name"])
            self.model = AutoDistributedModelForCausalLM.from_pretrained(selected_model["name"], torch_dtype=dtypes[self.config["inference_dtype_id"]])

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
        """
        Handle the completion of response generation.

        This method is called when the response generation thread has completed. It updates the `response_text` QTextEdit
        widget with the generated text, re-enables the generate button, and re-enables user input.

        Args:
            generated_text (str): The generated response text.

        """
        self.response_text.setPlainText(generated_text)
        self.generate_button.setText("Generate Response")
        self.generate_button.setEnabled(True)
        self.input_prompt.setEnabled(True)
        QCoreApplication.processEvents()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PetalsServiceMonitor()
    window.show()
    sys.exit(app.exec_())
