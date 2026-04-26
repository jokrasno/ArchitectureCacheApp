"""Cache View - editable cache table display"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class CacheView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_set = None
        self.highlighted_way = None
        self.tag_bits = 6
        self.num_sets = 256
        self.associativity = 1
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        
        title = QLabel("Cache")
        title.setStyleSheet("font-weight: bold; font-size: 13pt; color: #2c3e50; padding: 2px 0;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(True)
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

    def update_cache(self, cache_state: dict, associativity: int = 1,
                    highlighted_set: int = None, highlighted_way: int = None,
                    is_hit: bool = None, tag_bits: int = 6):
        self.highlighted_set = highlighted_set
        self.highlighted_way = highlighted_way
        self.tag_bits = tag_bits
        self.num_sets = len(cache_state)
        self.associativity = associativity
        
        if associativity == 1:
            self._update_direct_mapped(cache_state)
        else:
            self._update_set_associative(cache_state, associativity)

    def _update_direct_mapped(self, cache_state: dict):
        num_sets = len(cache_state)
        self.table.setRowCount(num_sets)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Valid", "Tag", "Data"])
        
        for set_idx in range(num_sets):
            display_row = num_sets - 1 - set_idx
            entry = cache_state[set_idx]['ways'][0]
            
            valid_item = QTableWidgetItem("1" if entry['valid'] else "0")
            valid_item.setFlags(valid_item.flags() | Qt.ItemFlag.ItemIsEditable)
            valid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(display_row, 0, valid_item)
            
            tag_item = QTableWidgetItem(f"{entry['tag']:0{self.tag_bits}b}" if entry['valid'] else "0" * self.tag_bits)
            tag_item.setFlags(tag_item.flags() | Qt.ItemFlag.ItemIsEditable)
            tag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(display_row, 1, tag_item)
            
            data_str = ", ".join(str(word) for word in entry['data']) if entry['valid'] else "0"
            data_item = QTableWidgetItem(data_str)
            data_item.setFlags(data_item.flags() | Qt.ItemFlag.ItemIsEditable)
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(display_row, 2, data_item)
            
            if set_idx == self.highlighted_set:
                color = QColor(255, 255, 150)
                for col in range(3):
                    item = self.table.item(display_row, col)
                    if item:
                        item.setBackground(color)
        
        self.table.setVerticalHeaderLabels([str(num_sets - 1 - i) for i in range(num_sets)])

    def _update_set_associative(self, cache_state: dict, associativity: int):
        num_sets = len(cache_state)
        num_cols = 1 + associativity * 3
        self.table.setRowCount(num_sets)
        self.table.setColumnCount(num_cols)
        
        headers = ["Set"]
        for way in range(associativity):
            headers.extend([f"V{way}", f"Tag{way}", f"Data{way}"])
        self.table.setHorizontalHeaderLabels(headers)
        
        for set_idx in range(num_sets):
            display_row = num_sets - 1 - set_idx
            set_item = QTableWidgetItem(str(set_idx))
            set_item.setFlags(set_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            set_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(display_row, 0, set_item)
            
            col = 1
            for way_idx, way_entry in enumerate(cache_state[set_idx]['ways']):
                valid_item = QTableWidgetItem("1" if way_entry['valid'] else "0")
                valid_item.setFlags(valid_item.flags() | Qt.ItemFlag.ItemIsEditable)
                valid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(display_row, col, valid_item)
                col += 1
                
                tag_item = QTableWidgetItem(f"{way_entry['tag']:0{self.tag_bits}b}" if way_entry['valid'] else "0" * self.tag_bits)
                tag_item.setFlags(tag_item.flags() | Qt.ItemFlag.ItemIsEditable)
                tag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(display_row, col, tag_item)
                col += 1
                
                data_str = ", ".join(str(word) for word in way_entry['data']) if way_entry['valid'] else "0"
                data_item = QTableWidgetItem(data_str)
                data_item.setFlags(data_item.flags() | Qt.ItemFlag.ItemIsEditable)
                data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(display_row, col, data_item)
                col += 1
                
                # Highlight entire set if way is None, or just the matching way
                if set_idx == self.highlighted_set and (
                    way_idx == self.highlighted_way or self.highlighted_way is None
                ):
                    color = QColor(255, 255, 150)
                    for c in range(col - 3, col):
                        item = self.table.item(display_row, c)
                        if item:
                            item.setBackground(color)

    def _column_offset(self, way_index: int) -> int:
        """Get the starting column for a given way index"""
        if self.associativity == 1:
            return 0
        return 1 + way_index * 3

    def get_slot_values(self, slot_idx: int, way_index: int = 0) -> tuple:
        """Get the current values in a cache slot as entered by user"""
        display_row = self.num_sets - 1 - slot_idx
        col = self._column_offset(way_index)

        valid_item = self.table.item(display_row, col)
        tag_item = self.table.item(display_row, col + 1)
        data_item = self.table.item(display_row, col + 2)

        try:
            valid = int(valid_item.text()) if valid_item else 0
        except ValueError:
            valid = 0

        try:
            tag = int(tag_item.text(), 2) if tag_item else 0
        except ValueError:
            tag = 0

        try:
            data_text = data_item.text() if data_item else "0"
            data = int(data_text.split(",")[0].strip())
        except ValueError:
            data = 0

        return valid, tag, data

    def set_slot_values(self, slot_idx: int, valid: int, tag: int, data: int,
                        way_index: int = 0):
        """Set the values in a cache slot (for auto-correction)"""
        display_row = self.num_sets - 1 - slot_idx
        col = self._column_offset(way_index)

        self.table.item(display_row, col).setText(str(valid))
        self.table.item(display_row, col + 1).setText(f"{tag:0{self.tag_bits}b}")
        self.table.item(display_row, col + 2).setText(str(data))

        for c in range(col, col + 3):
            item = self.table.item(display_row, c)
            if item:
                item.setBackground(QColor(144, 238, 144))
