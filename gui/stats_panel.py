"""Statistics Panel - hit/miss statistics display"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt


class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        
        self.hits_label = QLabel("Hits: 0")
        self.misses_label = QLabel("Misses: 0")
        self.hit_rate_label = QLabel("Hit Rate: 0.0%")
        self.operation_label = QLabel("Operation: 0 / 0")
        
        stats_layout.addWidget(self.hits_label)
        stats_layout.addWidget(self.misses_label)
        stats_layout.addWidget(self.hit_rate_label)
        stats_layout.addWidget(self.operation_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        layout.addStretch()
        self.setLayout(layout)

    def update_stats(self, hits: int, misses: int, current_op: int = 0, total_ops: int = 0):
        self.hits_label.setText(f"Hits: {hits}")
        self.misses_label.setText(f"Misses: {misses}")
        
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0.0
        self.hit_rate_label.setText(f"Hit Rate: {hit_rate:.1f}%")
        self.operation_label.setText(f"Operation: {current_op} / {total_ops}")
