"""Operation Panel - current operation display and student input"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QRadioButton, QButtonGroup, QPushButton,
                             QLineEdit, QTextEdit)
from PyQt6.QtCore import pyqtSignal


class OperationPanel(QWidget):
    check_answer = pyqtSignal()
    next_operation = pyqtSignal()
    previous_operation = pyqtSignal()
    reset_exercise = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_address = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Current Operation
        op_group = QGroupBox("Current Operation")
        op_layout = QVBoxLayout()
        self.operation_label = QLabel("No operation")
        self.operation_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        op_layout.addWidget(self.operation_label)
        
        address_layout = QHBoxLayout()
        self.address_label = QLabel("Address: -")
        address_layout.addWidget(self.address_label)
        self.go_to_address_button = QPushButton("Go to Address")
        self.go_to_address_button.setEnabled(False)
        address_layout.addWidget(self.go_to_address_button)
        op_layout.addLayout(address_layout)
        
        self.value_label = QLabel("Value: -")
        op_layout.addWidget(self.value_label)
        op_group.setLayout(op_layout)
        layout.addWidget(op_group)
        
        # Hit/Miss Selection
        hit_miss_group = QGroupBox("1. Hit or Miss?")
        hit_miss_layout = QHBoxLayout()
        self.hit_miss_group = QButtonGroup()
        self.hit_radio = QRadioButton("Hit")
        self.miss_radio = QRadioButton("Miss")
        self.hit_miss_group.addButton(self.hit_radio, 0)
        self.hit_miss_group.addButton(self.miss_radio, 1)
        hit_miss_layout.addWidget(self.hit_radio)
        hit_miss_layout.addWidget(self.miss_radio)
        hit_miss_group.setLayout(hit_miss_layout)
        layout.addWidget(hit_miss_group)
        
        # Address Decomposition
        decomp_group = QGroupBox("2. Address Decomposition (binary)")
        decomp_layout = QVBoxLayout()
        
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tag:"))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("binary")
        tag_layout.addWidget(self.tag_input)
        decomp_layout.addLayout(tag_layout)
        
        block_idx_layout = QHBoxLayout()
        block_idx_layout.addWidget(QLabel("Block Index:"))
        self.block_idx_input = QLineEdit()
        self.block_idx_input.setPlaceholderText("binary")
        block_idx_layout.addWidget(self.block_idx_input)
        decomp_layout.addLayout(block_idx_layout)
        
        block_off_layout = QHBoxLayout()
        self.block_off_label = QLabel("Block Offset:")
        self.block_off_input = QLineEdit()
        self.block_off_input.setPlaceholderText("binary")
        block_off_layout.addWidget(self.block_off_label)
        block_off_layout.addWidget(self.block_off_input)
        decomp_layout.addLayout(block_off_layout)
        self.block_off_label.setVisible(False)
        self.block_off_input.setVisible(False)
        
        byte_off_layout = QHBoxLayout()
        byte_off_layout.addWidget(QLabel("Byte Offset:"))
        self.byte_off_input = QLineEdit()
        self.byte_off_input.setPlaceholderText("binary")
        byte_off_layout.addWidget(self.byte_off_input)
        decomp_layout.addLayout(byte_off_layout)
        
        decomp_group.setLayout(decomp_layout)
        layout.addWidget(decomp_group)
        
        # Feedback
        feedback_group = QGroupBox("Feedback")
        feedback_layout = QVBoxLayout()
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setMaximumHeight(120)
        feedback_layout.addWidget(self.feedback_text)
        feedback_group.setLayout(feedback_layout)
        layout.addWidget(feedback_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.check_button = QPushButton("Check")
        self.check_button.clicked.connect(self.check_answer.emit)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_operation.emit)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_exercise.emit)
        
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)

    def update_operation(self, operation_type: str, address: int, value: int = None, block_size_words: int = 1):
        if operation_type == 'read':
            self.operation_label.setText("Read Operation")
            self.value_label.setText("Value: (to be read)")
        else:
            self.operation_label.setText("Write Operation")
            self.value_label.setText(f"Value: {value}")
        
        self.address_label.setText(f"Address: 0x{address:04X}")
        self.go_to_address_button.setEnabled(True)
        self.current_address = address
        
        self.block_off_label.setVisible(block_size_words > 1)
        self.block_off_input.setVisible(block_size_words > 1)
        
        # Clear inputs
        self.hit_radio.setChecked(False)
        self.miss_radio.setChecked(False)
        self.tag_input.clear()
        self.block_idx_input.clear()
        self.block_off_input.clear()
        self.byte_off_input.clear()
        self.feedback_text.clear()

    def set_go_to_address_callback(self, callback):
        self.go_to_address_button.clicked.connect(lambda: callback(self.current_address))

    def get_hit_miss_answer(self) -> bool:
        return self.hit_radio.isChecked()

    def get_address_decomposition(self) -> tuple:
        def parse(text):
            return int(text, 2) if text else 0
        try:
            return (parse(self.tag_input.text()), parse(self.block_idx_input.text()),
                    parse(self.block_off_input.text()), parse(self.byte_off_input.text()))
        except ValueError:
            return 0, 0, 0, 0

    def set_feedback(self, message: str, is_correct: bool = None):
        self.feedback_text.clear()
        if message:
            self.feedback_text.append(message)
            if is_correct is True:
                self.feedback_text.setStyleSheet("color: green;")
            elif is_correct is False:
                self.feedback_text.setStyleSheet("color: red;")
            else:
                self.feedback_text.setStyleSheet("")

    def clear_feedback(self):
        self.feedback_text.clear()
        self.feedback_text.setStyleSheet("")
