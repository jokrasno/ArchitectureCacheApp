"""Statistics Panel - hit/miss statistics display"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt


class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)
        
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(4)
        
        self.hits_label = QLabel("Hits: 0")
        self.hits_label.setStyleSheet("font-size: 10pt; color: #27ae60;")
        self.misses_label = QLabel("Misses: 0")
        self.misses_label.setStyleSheet("font-size: 10pt; color: #c0392b;")
        self.hit_rate_label = QLabel("Hit Rate: 0.0%")
        self.hit_rate_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        self.operation_label = QLabel("Problem: #1")
        self.operation_label.setStyleSheet("font-size: 10pt; color: #2c3e50;")
        
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
        if total_ops > 0:
            self.operation_label.setText(f"Operation: {current_op} / {total_ops}")
        else:
            self.operation_label.setText(f"Problem: #{current_op}")
