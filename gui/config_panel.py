"""Configuration Panel - cache parameter settings"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import pyqtSignal


class ConfigPanel(QWidget):
    config_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header
        header = QLabel("Cache Configuration")
        header.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2c3e50; padding: 4px 0;")
        layout.addWidget(header)
        
        # Cache Type
        cache_type_group = QGroupBox("Cache Type")
        cache_type_layout = QVBoxLayout()
        self.cache_type_combo = QComboBox()
        self.cache_type_combo.addItems(["Direct-Mapped", "Set-Associative"])
        self.cache_type_combo.currentTextChanged.connect(self.on_cache_type_changed)
        cache_type_layout.addWidget(self.cache_type_combo)
        cache_type_group.setLayout(cache_type_layout)
        layout.addWidget(cache_type_group)
        
        # Associativity
        self.associativity_group = QGroupBox("Ways (Associativity)")
        associativity_layout = QVBoxLayout()
        self.associativity_combo = QComboBox()
        self.associativity_combo.addItems(["2-way", "4-way", "8-way"])
        associativity_layout.addWidget(self.associativity_combo)
        self.associativity_group.setLayout(associativity_layout)
        self.associativity_group.setVisible(False)
        layout.addWidget(self.associativity_group)
        
        # Cache Size - default to 8 slots for beginners
        cache_size_group = QGroupBox("Cache Size")
        cache_size_layout = QVBoxLayout()
        self.cache_size_label = QLabel("Number of slots:")
        cache_size_layout.addWidget(self.cache_size_label)
        self.cache_size_combo = QComboBox()
        self.cache_size_combo.addItems(
            ["2", "4", "8", "16", "32", "64", "128", "256", "512", "1024"])
        self.cache_size_combo.setCurrentText("8")
        cache_size_layout.addWidget(self.cache_size_combo)
        cache_size_group.setLayout(cache_size_layout)
        layout.addWidget(cache_size_group)
        
        # Block Size
        block_size_group = QGroupBox("Block Size")
        block_size_layout = QVBoxLayout()
        self.block_size_combo = QComboBox()
        self.block_size_combo.addItems(["1 word", "2 words", "4 words", "8 words"])
        block_size_layout.addWidget(self.block_size_combo)
        block_size_group.setLayout(block_size_layout)
        layout.addWidget(block_size_group)
        
        # Write Policy
        write_policy_group = QGroupBox("Write Policy")
        write_policy_layout = QVBoxLayout()
        self.write_policy_combo = QComboBox()
        self.write_policy_combo.addItems(["Write-Through", "Write-Back"])
        write_policy_layout.addWidget(self.write_policy_combo)
        write_policy_group.setLayout(write_policy_layout)
        layout.addWidget(write_policy_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.apply_button.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; "
            "font-weight: bold; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2980b9; }"
        )
        self.apply_button.clicked.connect(self.apply_config)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(
            "QPushButton { background-color: #f5f7fa; color: #2c3e50; "
            "border: 1px solid #bdc3c7; padding: 6px 12px; border-radius: 4px; }"
        )
        self.reset_button.clicked.connect(self.reset_config)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)

    def on_cache_type_changed(self, text):
        self.associativity_group.setVisible(text == "Set-Associative")

    def get_config(self) -> dict:
        cache_type = self.cache_type_combo.currentText()
        associativity = 1
        if cache_type == "Set-Associative":
            associativity = int(self.associativity_combo.currentText().split("-")[0])
        
        block_size = int(self.block_size_combo.currentText().split()[0])
        write_policy = self.write_policy_combo.currentText().lower()
        
        return {
            'cache_type': cache_type,
            'associativity': associativity,
            'cache_size_slots': int(self.cache_size_combo.currentText()),
            'block_size_words': block_size,
            'write_policy': write_policy
        }

    def apply_config(self):
        self.config_changed.emit(self.get_config())

    def reset_config(self):
        self.cache_type_combo.setCurrentIndex(0)
        self.associativity_combo.setCurrentIndex(0)
        self.cache_size_combo.setCurrentText("8")
        self.block_size_combo.setCurrentIndex(0)
        self.write_policy_combo.setCurrentIndex(0)
        self.apply_config()
