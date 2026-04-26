"""Memory View - editable main memory display"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class MemoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_addresses = set()
        self.memory_contents = {}
        self.highlighted_address = None
        self.is_write_operation = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        
        title = QLabel("Main Memory")
        title.setStyleSheet("font-weight: bold; font-size: 13pt; color: #2c3e50; padding: 2px 0;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Address", "Value"])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { "
            "  background-color: #ffffff; "
            "  alternate-background-color: #f6f8fa; "
            "  color: #1f2933; "
            "  gridline-color: #d5d8dc; "
            "  font-size: 10pt; "
            "} "
            "QTableWidget::item { color: #1f2933; padding: 3px 6px; }"
            "QTableWidget::item:alternate { background-color: #f8f9fa; }"
            "QHeaderView::section { background-color: #5d6d7e; color: white; "
            "padding: 4px; border: 1px solid #4a5568; font-weight: bold; font-size: 9pt; }"
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_memory(self, memory_contents: dict, recent_addresses: set = None, 
                     highlighted_address: int = None, is_write: bool = False):
        self.memory_contents = memory_contents.copy()
        self.recent_addresses = recent_addresses.copy() if recent_addresses else set()
        self.highlighted_address = highlighted_address
        self.is_write_operation = is_write
        self._refresh_display()

    def _refresh_display(self):
        addresses_to_show = set(self.memory_contents.keys()) | self.recent_addresses
        if self.highlighted_address is not None:
            addresses_to_show.add(self.highlighted_address)
        
        sorted_addresses = sorted(addresses_to_show, reverse=True)
        self.table.setRowCount(len(sorted_addresses))
        
        for row, addr in enumerate(sorted_addresses):
            addr_item = QTableWidgetItem(f"0x{addr:04X}")
            addr_item.setFlags(addr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            addr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, addr_item)
            
            value = self.memory_contents.get(addr, 0)
            value_item = QTableWidgetItem(str(value))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Make value editable for write operations on the highlighted address
            if addr == self.highlighted_address and self.is_write_operation:
                value_item.setFlags(value_item.flags() | Qt.ItemFlag.ItemIsEditable)
                value_item.setBackground(QColor(255, 200, 200))  # Light red for write target
            else:
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.table.setItem(row, 1, value_item)
            
            if addr in self.recent_addresses and addr != self.highlighted_address:
                addr_item.setBackground(Qt.GlobalColor.yellow)
                value_item.setBackground(Qt.GlobalColor.yellow)

    def get_value_at_address(self, address: int) -> int:
        """Get the value entered by user at a specific address"""
        for row in range(self.table.rowCount()):
            addr_item = self.table.item(row, 0)
            if addr_item:
                addr_value = int(addr_item.text(), 16)
                if addr_value == address:
                    value_item = self.table.item(row, 1)
                    try:
                        return int(value_item.text()) if value_item else 0
                    except:
                        return 0
        return 0

    def set_value_at_address(self, address: int, value: int):
        """Set the value at a specific address (for auto-correction)"""
        for row in range(self.table.rowCount()):
            addr_item = self.table.item(row, 0)
            if addr_item:
                addr_value = int(addr_item.text(), 16)
                if addr_value == address:
                    value_item = self.table.item(row, 1)
                    if value_item:
                        value_item.setText(str(value))
                        value_item.setBackground(QColor(144, 238, 144))  # Green for corrected
                    return

    def scroll_to_address(self, address: int):
        for row in range(self.table.rowCount()):
            addr_item = self.table.item(row, 0)
            if addr_item:
                addr_value = int(addr_item.text(), 16)
                if addr_value == address:
                    self.table.scrollToItem(addr_item)
                    return
