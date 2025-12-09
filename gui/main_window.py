"""Main Window for Cache Learning Application"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QSplitter, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
import random
from gui.config_panel import ConfigPanel
from gui.cache_view import CacheView
from gui.memory_view import MemoryView
from gui.operation_panel import OperationPanel
from gui.stats_panel import StatsPanel
from cache_simulator import CacheSimulator
from memory_simulator import MemorySimulator
from exercise_manager import ExerciseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cache = None
        self.memory = None
        self.exercise_manager = None
        self.procedural_mode = True
        self.procedural_count = 0
        self.init_ui()
        self.setup_default_config()

    def init_ui(self):
        self.setWindowTitle("Cache Learning Application")
        self.setGeometry(100, 100, 1400, 900)
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        self.status_label = QLabel("Procedural Mode - Problem #1")
        self.status_label.setStyleSheet("background-color: #FE9900; padding: 5px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        self.config_panel = ConfigPanel()
        self.cache_view = CacheView()
        self.memory_view = MemoryView()
        self.operation_panel = OperationPanel()
        self.stats_panel = StatsPanel()
        
        self.config_panel.config_changed.connect(self.on_config_changed)
        self.operation_panel.check_answer.connect(self.on_check_answer)
        self.operation_panel.next_operation.connect(self.on_next_operation)
        self.operation_panel.previous_operation.connect(self.on_previous_operation)
        self.operation_panel.reset_exercise.connect(self.on_reset_exercise)
        self.operation_panel.set_go_to_address_callback(self.on_go_to_address)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.config_panel)
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(250)
        
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        center_splitter.addWidget(self.cache_view)
        center_splitter.addWidget(self.memory_view)
        center_splitter.setSizes([400, 300])
        
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.operation_panel)
        right_layout.addWidget(self.stats_panel)
        right_widget.setLayout(right_layout)
        right_widget.setMaximumWidth(400)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(center_splitter)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([250, 800, 400])
        
        content_layout = QHBoxLayout()
        content_layout.addWidget(main_splitter)
        main_layout.addLayout(content_layout)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Reset Cache", self.on_reset_exercise)
        file_menu.addSeparator()
        file_menu.addAction("Randomize Memory", self.on_randomize_memory)
        file_menu.addAction("Clear Memory", self.on_clear_memory)
        file_menu.addAction("Clear Cache", self.on_clear_cache)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.on_about)

    def setup_default_config(self):
        self.config_panel.apply_config()

    def on_config_changed(self, config: dict):
        self.memory = MemorySimulator()
        self.cache = CacheSimulator(
            cache_size_slots=config['cache_size_slots'],
            block_size_words=config['block_size_words'],
            associativity=config['associativity'],
            write_policy=config['write_policy'],
            memory_simulator=self.memory
        )
        self.exercise_manager = ExerciseManager(self.cache, self.memory)
        self.procedural_mode = True
        self.procedural_count = 0
        
        self.update_block_offset_visibility()
        self.update_status_message()
        self.generate_procedural_problem()
        self.update_all_displays()

    def update_block_offset_visibility(self):
        if self.cache:
            visible = self.cache.block_size_words > 1
            self.operation_panel.block_off_label.setVisible(visible)
            self.operation_panel.block_off_input.setVisible(visible)

    def on_go_to_address(self, address: int):
        self.memory_view.scroll_to_address(address)

    def on_randomize_memory(self):
        if not self.memory:
            QMessageBox.warning(self, "Warning", "Please configure cache first.")
            return
        
        total_addresses = 65536 // 4
        percentage = random.uniform(0.5, 1.0)
        num_addresses = int(total_addresses * percentage)
        all_addresses = list(range(0, 65536, 4))
        selected = random.sample(all_addresses, num_addresses)
        
        for addr in selected:
            self.memory.write(addr, random.randint(1, 1000))
        
        self.generate_procedural_problem()
        self.update_all_displays()
        QMessageBox.information(self, "Memory Randomized", 
            f"Populated {num_addresses} addresses ({percentage*100:.1f}%).")

    def on_clear_memory(self):
        if not self.memory:
            QMessageBox.warning(self, "Warning", "Please configure cache first.")
            return
        
        reply = QMessageBox.question(self, "Clear Memory", 
            "Clear all memory contents?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.memory.reset()
            self.generate_procedural_problem()
            self.update_all_displays()

    def on_clear_cache(self):
        if not self.cache:
            QMessageBox.warning(self, "Warning", "Please configure cache first.")
            return
        
        self.cache.reset()
        self.update_all_displays()

    def generate_procedural_problem(self):
        if not self.exercise_manager or not self.procedural_mode:
            return
        
        op = self.exercise_manager.generate_random_operation()
        self.exercise_manager.set_procedural_operation(op)
        self.update_operation_display()

    def update_status_message(self):
        self.status_label.setText(f"Procedural Mode - Problem #{self.procedural_count + 1}")
        self.status_label.setStyleSheet("background-color: #FE9900; padding: 5px; font-weight: bold;")

    def on_check_answer(self):
        if not self.exercise_manager:
            self.operation_panel.set_feedback("Please configure cache first.", False)
            return
        
        op = self.exercise_manager.get_current_operation()
        if not op:
            self.operation_panel.set_feedback("No current operation.", False)
            return
        
        is_write = op.operation_type == 'write'
        
        # Get student's form answers
        hit_miss_answer = self.operation_panel.get_hit_miss_answer()
        tag, block_idx, block_off, byte_off = self.operation_panel.get_address_decomposition()
        
        # Get correct values
        correct_tag, correct_bi, correct_bo, correct_byo = \
            self.exercise_manager.get_correct_address_decomposition()
        
        # Calculate expected hit/miss from current cache state
        cache_state = self.cache.get_cache_state()
        slot_entry = cache_state[correct_bi]['ways'][0]
        expected_hit = slot_entry['valid'] and slot_entry['tag'] == correct_tag
        
        # Validate form answers
        hit_miss_correct = (hit_miss_answer == expected_hit)
        decomp_correct = (tag == correct_tag and block_idx == correct_bi and 
                         block_off == correct_bo and byte_off == correct_byo)
        
        # Get what student entered in cache table
        student_valid, student_tag, student_data = self.cache_view.get_slot_values(correct_bi)
        
        if is_write:
            # WRITE operation: check memory AND cache
            write_value = op.value
            
            # Expected: memory should have the write value
            student_memory_value = self.memory_view.get_value_at_address(op.address)
            memory_correct = (student_memory_value == write_value)
            
            # For write-through: cache updated with write value
            # Expected cache state after write
            expected_cache_data = write_value
            expected_valid = 1
            expected_cache_tag = correct_tag
            
            cache_valid_correct = (student_valid == expected_valid)
            cache_tag_correct = (student_tag == expected_cache_tag)
            cache_data_correct = (student_data == expected_cache_data)
            cache_table_correct = cache_valid_correct and cache_tag_correct and cache_data_correct
            
            all_correct = hit_miss_correct and decomp_correct and cache_table_correct and memory_correct
            
        else:
            # READ operation: check cache only
            expected_data = self.memory.read(op.address)
            expected_valid = 1
            expected_cache_tag = correct_tag
            
            cache_valid_correct = (student_valid == expected_valid)
            cache_tag_correct = (student_tag == expected_cache_tag)
            cache_data_correct = (student_data == expected_data)
            cache_table_correct = cache_valid_correct and cache_tag_correct and cache_data_correct
            
            memory_correct = True  # Not checked for reads
            expected_cache_data = expected_data
            
            all_correct = hit_miss_correct and decomp_correct and cache_table_correct
        
        attempts = self.exercise_manager.get_attempts_for_current() + 1
        self.exercise_manager.attempts_per_question[self.exercise_manager.current_operation_index] = attempts
        
        if all_correct:
            # Update the actual simulators
            self.exercise_manager.execute_current_operation()
            
            self.exercise_manager.mark_current_answered()
            self.exercise_manager.attempts_per_question[self.exercise_manager.current_operation_index] = 0
            
            # Show success pop-up
            op_type = "Write" if is_write else "Read"
            msg = (f"★ Great job! ★\n\n"
                   f"{op_type} {'Hit' if expected_hit else 'Miss'}!\n"
                   f"Cache slot {correct_bi} correctly updated:\n"
                   f"  Valid = 1\n"
                   f"  Tag = {correct_tag:0{self.cache.tag_bits}b}\n"
                   f"  Data = {expected_cache_data}")
            if is_write:
                msg += f"\n\nMemory at 0x{op.address:04X} = {op.value}"
            
            QMessageBox.information(self, "Correct!", msg)
            
            self.operation_panel.set_feedback("✓ Correct! Moving to next problem...", True)
            
            self.procedural_count += 1
            self.update_status_message()
            self.generate_procedural_problem()
            self.update_all_displays()
            
        elif attempts >= self.exercise_manager.max_attempts:
            # Auto-correct everything
            self.cache_view.set_slot_values(correct_bi, 1, correct_tag, expected_cache_data)
            
            if is_write:
                self.memory_view.set_value_at_address(op.address, op.value)
            
            # Update actual simulators
            self.exercise_manager.execute_current_operation()
            
            # Fill in correct form answers
            if expected_hit:
                self.operation_panel.hit_radio.setChecked(True)
            else:
                self.operation_panel.miss_radio.setChecked(True)
            self.operation_panel.tag_input.setText(f"{correct_tag:0{self.cache.tag_bits}b}")
            self.operation_panel.block_idx_input.setText(f"{correct_bi:0{self.cache.block_index_bits}b}")
            self.operation_panel.block_off_input.setText(f"{correct_bo:0{self.cache.block_offset_bits}b}")
            self.operation_panel.byte_off_input.setText(f"{correct_byo:0{self.cache.byte_offset_bits}b}")
            
            feedback_parts = ["✗ Out of attempts. Correct answers filled in:\n"]
            if not hit_miss_correct:
                feedback_parts.append(f"  • Hit/Miss: {'Hit' if expected_hit else 'Miss'}")
            if not decomp_correct:
                feedback_parts.append(f"  • Tag: {correct_tag:0{self.cache.tag_bits}b}")
                feedback_parts.append(f"  • Block Index: {correct_bi}")
            if not cache_table_correct:
                feedback_parts.append(f"\nCache slot {correct_bi}:")
                feedback_parts.append(f"  • Valid = 1")
                feedback_parts.append(f"  • Tag = {correct_tag:0{self.cache.tag_bits}b}")
                feedback_parts.append(f"  • Data = {expected_cache_data}")
            if is_write and not memory_correct:
                feedback_parts.append(f"\nMemory at 0x{op.address:04X} = {op.value}")
            
            self.operation_panel.set_feedback("\n".join(feedback_parts), False)
            
            self.exercise_manager.mark_current_answered()
            
            self.procedural_count += 1
            self.update_status_message()
            self.generate_procedural_problem()
            self.update_all_displays()
            
        else:
            # Wrong answer, still have attempts
            feedback_parts = ["✗ Incorrect. Check:\n"]
            
            if not hit_miss_correct:
                feedback_parts.append("  • Hit/Miss answer")
            if tag != correct_tag:
                feedback_parts.append("  • Tag decomposition")
            if block_idx != correct_bi:
                feedback_parts.append("  • Block Index")
            if byte_off != correct_byo:
                feedback_parts.append("  • Byte Offset")
            
            if not cache_valid_correct:
                feedback_parts.append(f"  • Cache slot {correct_bi} Valid bit")
            if not cache_tag_correct:
                feedback_parts.append(f"  • Cache slot {correct_bi} Tag")
            if not cache_data_correct:
                feedback_parts.append(f"  • Cache slot {correct_bi} Data")
            
            if is_write and not memory_correct:
                feedback_parts.append(f"  • Memory value at 0x{op.address:04X}")
            
            remaining = self.exercise_manager.max_attempts - attempts
            feedback_parts.append(f"\n{remaining} attempt(s) remaining")
            
            self.operation_panel.set_feedback("\n".join(feedback_parts), False)

    def on_next_operation(self):
        if not self.exercise_manager:
            return
        
        if self.exercise_manager.is_current_answered():
            self.procedural_count += 1
            self.update_status_message()
            self.generate_procedural_problem()
            self.update_all_displays()
        else:
            self.operation_panel.set_feedback("Answer the current problem first!", False)

    def on_previous_operation(self):
        self.operation_panel.set_feedback("No previous in procedural mode.", False)

    def on_reset_exercise(self):
        if self.cache:
            self.cache.reset()
        self.procedural_count = 0
        if self.exercise_manager:
            self.exercise_manager.attempts_per_question = {}
            self.exercise_manager.current_answered_correctly = False
        self.generate_procedural_problem()
        self.update_status_message()
        self.update_all_displays()

    def on_about(self):
        QMessageBox.about(self, "About", "Cache Learning Application\n\nA tool for learning cache memory concepts.")

    def update_operation_display(self):
        if not self.exercise_manager:
            return
        
        op = self.exercise_manager.get_current_operation()
        block_size = self.cache.block_size_words if self.cache else 1
        
        if op:
            self.operation_panel.update_operation(op.operation_type, op.address, op.value, block_size)
        else:
            self.operation_panel.operation_label.setText("No operation")
            self.operation_panel.address_label.setText("Address: -")
            self.operation_panel.value_label.setText("Value: -")
            self.operation_panel.go_to_address_button.setEnabled(False)

    def update_all_displays(self, is_hit: bool = None):
        if not self.cache or not self.memory:
            return
        
        cache_state = self.cache.get_cache_state()
        op = self.exercise_manager.get_current_operation() if self.exercise_manager else None
        
        highlighted_set = None
        highlighted_address = None
        is_write = False
        
        if op:
            tag, block_idx, _, _ = self.cache.calculate_address_components(op.address)
            highlighted_set = block_idx
            highlighted_address = op.address
            is_write = op.operation_type == 'write'
        
        self.cache_view.update_cache(cache_state, self.cache.associativity,
                                     highlighted_set, 0, is_hit, self.cache.tag_bits)
        
        memory_contents = {addr: self.memory.read(addr) for addr in self.memory.get_all_addresses()}
        recent = {op.address} if op else set()
        self.memory_view.update_memory(memory_contents, recent, highlighted_address, is_write)
        
        stats = self.cache.get_statistics()
        self.stats_panel.update_stats(stats['hits'], stats['misses'], 
                                      self.procedural_count + 1, 0)
