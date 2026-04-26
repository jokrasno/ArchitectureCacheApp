"""Integration tests for procedural mode — tests MainWindow.on_check_answer flow.

These tests exercise the full answer-checking pipeline including:
- Hit/miss detection across all ways
- Address decomposition validation
- Cache table editing and validation
- Memory value editing and validation
- Write-through vs write-back miss behavior
- Attempt tracking and auto-correction
"""

import sys
import os
import pytest
from unittest.mock import patch

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.cache_view import CacheView
from gui.operation_panel import OperationPanel
from gui.memory_view import MemoryView
from gui.config_panel import ConfigPanel
from cache_simulator import CacheSimulator
from memory_simulator import MemorySimulator
from exercise_manager import ExerciseManager, ExerciseOperation


# ---------------------------------------------------------------------------
# QApplication singleton — created once for all tests in this module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication if one doesn't already exist."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def window(qapp):
    """Create a MainWindow for testing. Suppresses QMessageBox popups."""
    with patch.object(qapp, 'processEvents'):
        w = MainWindow()
    yield w


@pytest.fixture
def window_with_data(window):
    """MainWindow with some memory values pre-loaded."""
    window.memory.write(0x0000, 42)
    window.memory.write(0x0100, 100)
    window.memory.write(0x1000, 200)
    return window


# Helper: inject a specific operation into the exercise manager and update display
def inject_operation(window, op_type, address, value=None):
    op = ExerciseOperation(op_type, address, value)
    window.exercise_manager.set_procedural_operation(op)
    window.update_operation_display()
    window.update_all_displays()
    return op


# Helper: fill in the student's answers in the GUI
def fill_answers(window, hit, tag, block_idx, block_off, byte_off):
    if hit:
        window.operation_panel.hit_radio.setChecked(True)
        window.operation_panel.miss_radio.setChecked(False)
    else:
        window.operation_panel.hit_radio.setChecked(False)
        window.operation_panel.miss_radio.setChecked(True)
    window.operation_panel.tag_input.setText(tag)
    window.operation_panel.block_idx_input.setText(block_idx)
    window.operation_panel.block_off_input.setText(block_off)
    window.operation_panel.byte_off_input.setText(byte_off)


# Helper: fill in a cache slot in the cache table
def fill_cache_slot(window, slot_idx, valid, tag, data, way_index=0):
    window.cache_view.set_slot_values(slot_idx, valid, tag, data, way_index)


# Helper: fill in a memory value in the memory table
def fill_memory_value(window, address, value):
    window.memory_view.set_value_at_address(address, value)


# Helper: format an integer as binary with leading zeros
def fmtb(value, bits):
    return format(value, f'0{bits}b')


# ===========================================================================
# Read operation tests
# ===========================================================================

class TestReadHit:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_read_hit(self, mock_gen, mock_msg, window_with_data):
        w = window_with_data
        # Load address 0x0000 into cache first
        w.cache.read(0x0000)
        w.update_all_displays()

        op = inject_operation(w, 'read', 0x0000)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 42)
        fill_memory_value(w, 0x0000, 42)  # not checked for reads but won't hurt

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert "Correct" in mock_msg.call_args[0][1] or "Correct" in mock_msg.call_args[0][2]
        assert w.exercise_manager.is_current_answered()


class TestReadMiss:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_read_miss(self, mock_gen, mock_msg, window_with_data):
        w = window_with_data
        # Don't pre-load — 0x0100 is not in cache
        op = inject_operation(w, 'read', 0x0100)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0100)

        fill_answers(w, hit=False,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 100)  # memory has 100 at 0x0100

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()


# ===========================================================================
# Write operation tests — write-through
# ===========================================================================

class TestWriteThroughHit:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_write_hit_wt(self, mock_gen, mock_msg, window):
        w = window
        w.cache.read(0x0000)  # load into cache
        w.update_all_displays()

        op = inject_operation(w, 'write', 0x0000, 99)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 99)
        fill_memory_value(w, 0x0000, 99)

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()
        # Verify simulator was updated
        assert w.memory.read(0x0000) == 99


class TestWriteThroughMiss:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_wt_miss_no_write_allocate(self, mock_gen, mock_msg, window):
        """Write-through miss: only memory updated, cache unchanged."""
        w = window
        assert w.cache.write_policy == 'write-through'

        op = inject_operation(w, 'write', 0x0000, 77)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=False,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        # For write-through miss, cache should NOT change — so we don't touch it
        # But we must fill memory
        fill_memory_value(w, 0x0000, 77)

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()
        # Verify memory was written
        assert w.memory.read(0x0000) == 77


# ===========================================================================
# Write operation tests — write-back
# ===========================================================================

class TestWriteBackHit:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_write_hit_wb(self, mock_gen, mock_msg, qapp):
        w = MainWindow()
        # Configure write-back
        config = {
            'cache_type': 'Direct-Mapped',
            'associativity': 1,
            'cache_size_slots': 256,
            'block_size_words': 1,
            'write_policy': 'write-back',
        }
        w.on_config_changed(config)
        assert w.cache.write_policy == 'write-back'

        w.cache.read(0x0000)
        w.update_all_displays()

        op = inject_operation(w, 'write', 0x0000, 55)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 55)

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()
        # Memory should NOT be updated (write-back)
        assert w.memory.read(0x0000) == 0


class TestWriteBackMiss:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_correct_wb_miss_write_allocate(self, mock_gen, mock_msg, qapp):
        """Write-back miss: block allocated in cache, memory unchanged."""
        w = MainWindow()
        config = {
            'cache_type': 'Direct-Mapped',
            'associativity': 1,
            'cache_size_slots': 256,
            'block_size_words': 1,
            'write_policy': 'write-back',
        }
        w.on_config_changed(config)

        op = inject_operation(w, 'write', 0x0000, 88)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=False,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 88)

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()
        # Memory should NOT be updated (write-back, dirty)
        assert w.memory.read(0x0000) == 0


# ===========================================================================
# Attempt tracking and auto-correction
# ===========================================================================

class TestAttempts:

    def test_first_wrong_answer_still_has_attempts(self, window):
        w = window
        op = inject_operation(w, 'read', 0x0000)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        # Wrong hit/miss answer
        fill_answers(w, hit=True,  # wrong — should be miss
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 0)

        w.on_check_answer()
        assert not w.exercise_manager.is_current_answered()
        feedback = w.operation_panel.feedback_text.toPlainText()
        assert "Incorrect" in feedback
        assert "attempt(s) remaining" in feedback

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_two_wrong_answers_triggers_autocorrect(self, mock_gen, mock_msg, window):
        w = window
        op = inject_operation(w, 'read', 0x0000)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        # First wrong attempt — wrong hit/miss
        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, tag, 0)
        w.on_check_answer()

        # Verify first attempt was wrong but not auto-corrected
        assert not w.exercise_manager.is_current_answered()

        # Second wrong attempt — wrong tag
        fill_answers(w, hit=False,
                     tag='0' * w.cache.tag_bits,  # wrong tag
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, 0, 0)
        w.on_check_answer()

        # After max attempts, auto-correct triggers and marks as answered
        assert w.exercise_manager.is_current_answered()

    def test_autocorrect_keeps_feedback_visible_until_next(self, window):
        w = window
        inject_operation(w, 'read', 0x0000)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, tag, 99)
        w.on_check_answer()

        fill_answers(w, hit=False,
                     tag='1' * w.cache.tag_bits,
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, tag, 99)
        w.on_check_answer()

        feedback = w.operation_panel.feedback_text.toPlainText()
        assert w.exercise_manager.is_current_answered()
        assert "Out of attempts" in feedback
        assert w.procedural_count == 0


# ===========================================================================
# Set-associative integration
# ===========================================================================

class TestSetAssociativeIntegration:

    @patch('gui.main_window.QMessageBox.information')
    @patch.object(MainWindow, 'generate_procedural_problem')
    def test_2way_read_hit_in_way1(self, mock_gen, mock_msg, qapp):
        """Hit detection should find data in way 1, not just way 0."""
        w = MainWindow()
        config = {
            'cache_type': 'Set-Associative',
            'associativity': 2,
            'cache_size_slots': 256,
            'block_size_words': 1,
            'write_policy': 'write-through',
        }
        w.on_config_changed(config)

        # Load two addresses into the same set (both ways)
        addr1 = 0x0000
        addr2 = 0x0400  # same set as addr1 (bi=0, 256 sets, mask=0xFF)
        w.memory.write(addr1, 42)
        w.memory.write(addr2, 99)
        w.cache.read(addr1)
        w.cache.read(addr2)
        w.update_all_displays()

        # Now test a read to addr2 — should be a hit (in way 1)
        op = inject_operation(w, 'read', addr2)
        tag, bi, bo, byo = w.cache.calculate_address_components(addr2)

        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        # Need to fill the correct way's cache slot
        state = w.cache.get_cache_state()
        ways = state[bi]['ways']
        way_idx = 0
        for i, way in enumerate(ways):
            if way['valid'] and way['tag'] == tag:
                way_idx = i
                break

        fill_cache_slot(w, bi, 1, tag, 99, way_index=way_idx)

        w.on_check_answer()
        mock_msg.assert_called_once()
        assert w.exercise_manager.is_current_answered()


# ===========================================================================
# Config change and reset
# ===========================================================================

class TestConfigAndReset:

    def test_config_change_resets_everything(self, window):
        w = window
        w.memory.write(0x0000, 42)
        w.cache.read(0x0000)
        w.procedural_count = 5

        config = {
            'cache_type': 'Direct-Mapped',
            'associativity': 1,
            'cache_size_slots': 256,
            'block_size_words': 1,
            'write_policy': 'write-through',
        }
        w.on_config_changed(config)
        assert w.procedural_count == 0
        assert w.cache.hits == 0
        assert w.cache.misses == 0

    def test_reset_exercise(self, window):
        w = window
        w.procedural_count = 10
        w.cache.read(0x0000)
        w.on_reset_exercise()
        assert w.procedural_count == 0
        assert w.cache.hits == 0
        assert w.cache.misses == 0

    @patch('gui.main_window.QMessageBox.information')
    def test_procedural_count_advances_on_correct(self, mock_msg, window):
        w = window
        assert w.procedural_count == 0

        op = inject_operation(w, 'read', 0x0000)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        fill_answers(w, hit=False,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))

        fill_cache_slot(w, bi, 1, tag, 0)

        w.on_check_answer()
        assert w.procedural_count == 1

    def test_on_next_without_answer(self, window):
        w = window
        inject_operation(w, 'read', 0x0000)
        w.on_next_operation()
        feedback = w.operation_panel.feedback_text.toPlainText()
        assert "Answer the current problem" in feedback
        assert w.procedural_count == 0


# ===========================================================================
# CacheView and MemoryView helpers
# ===========================================================================

class TestViewHelpers:

    def test_cache_view_column_offset_direct(self, qapp):
        cv = CacheView()
        cv.associativity = 1
        assert cv._column_offset(0) == 0

    def test_cache_view_column_offset_2way(self, qapp):
        cv = CacheView()
        cv.associativity = 2
        assert cv._column_offset(0) == 1  # after "Set" column
        assert cv._column_offset(1) == 4  # skip Set + V0+Tag0+Data0

    def test_cache_view_column_offset_4way(self, qapp):
        cv = CacheView()
        cv.associativity = 4
        assert cv._column_offset(0) == 1
        assert cv._column_offset(1) == 4
        assert cv._column_offset(2) == 7
        assert cv._column_offset(3) == 10

    def test_get_slot_values_default_way(self, qapp):
        """get_slot_values with default way_index=0 works for direct-mapped."""
        cv = CacheView()
        cv.associativity = 1
        cv.num_sets = 4
        cv.tag_bits = 6
        # Simulate a direct-mapped table
        cv.table.setRowCount(4)
        cv.table.setColumnCount(3)
        for row in range(4):
            for col in range(3):
                from PyQt6.QtWidgets import QTableWidgetItem
                cv.table.setItem(row, col, QTableWidgetItem("0"))
        # Set row 3 (slot 0, since display is reversed) to have values
        cv.table.item(3, 0).setText("1")
        cv.table.item(3, 1).setText("000101")
        cv.table.item(3, 2).setText("42")
        valid, tag, data = cv.get_slot_values(0)
        assert valid == 1
        assert tag == 0b000101
        assert data == 42

    def test_memory_view_get_value(self, qapp):
        mv = MemoryView()
        mv.update_memory({0x0000: 42, 0x0004: 99}, set(), None, False)
        assert mv.get_value_at_address(0x0000) == 42
        assert mv.get_value_at_address(0x0004) == 99
        assert mv.get_value_at_address(0x0008) == 0  # not in table

    def test_memory_view_set_value(self, qapp):
        mv = MemoryView()
        mv.update_memory({0x0000: 42}, set(), None, False)
        mv.set_value_at_address(0x0000, 99)
        assert mv.get_value_at_address(0x0000) == 99


# ===========================================================================
# Bug-fix regression tests
# ===========================================================================

class TestBugFixHitMissUnanswered:
    """Bug: get_hit_miss_answer returned False when neither radio selected,
       silently treating unanswered as Miss."""

    def test_hit_miss_none_when_unselected(self, qapp):
        """get_hit_miss_answer returns None when neither radio is selected."""
        op = OperationPanel()
        op.hit_radio.setChecked(False)
        op.miss_radio.setChecked(False)
        assert op.get_hit_miss_answer() is None

    def test_hit_miss_true(self, qapp):
        op = OperationPanel()
        op.hit_radio.setChecked(True)
        assert op.get_hit_miss_answer() is True

    def test_hit_miss_false(self, qapp):
        op = OperationPanel()
        op.miss_radio.setChecked(True)
        assert op.get_hit_miss_answer() is False

    def test_update_operation_clears_previous_hit_miss_choice(self, qapp):
        """A new problem should not inherit the previous Hit/Miss choice."""
        op = OperationPanel()
        op.hit_radio.setChecked(True)
        op.tag_input.setText("101")

        op.update_operation('read', 0x0100)

        assert op.get_hit_miss_answer() is None
        assert op.tag_input.text() == ""

    def test_check_answer_rejects_unselected(self, window):
        """Checking with no Hit/Miss selected gives a feedback message, not a
        silent false."""
        w = window
        inject_operation(w, 'read', 0x0000)
        # Deliberately don't select hit or miss
        w.operation_panel.hit_radio.setChecked(False)
        w.operation_panel.miss_radio.setChecked(False)
        w.on_check_answer()
        feedback = w.operation_panel.feedback_text.toPlainText()
        assert "select" in feedback.lower() or "hit or miss" in feedback.lower()
        assert not w.exercise_manager.is_current_answered()


class TestBugFixWriteBackAutocorrectMemory:
    """Bug: autocorrect for write-back write hits visually updated memory
       even though write-back should keep memory unchanged until eviction."""

    def test_wb_hit_autocorrect_keeps_memory_unchanged(self, qapp):
        """After autocorrect on a write-back hit, memory should still be 0."""
        w = MainWindow()
        config = {
            'cache_type': 'Direct-Mapped',
            'associativity': 1,
            'cache_size_slots': 256,
            'block_size_words': 1,
            'write_policy': 'write-back',
        }
        w.on_config_changed(config)
        w.memory.write(0x0000, 10)
        w.cache.read(0x0000)  # load into cache
        w.update_all_displays()

        op = inject_operation(w, 'write', 0x0000, 55)
        tag, bi, bo, byo = w.cache.calculate_address_components(0x0000)

        # First wrong attempt
        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, tag, 999)  # wrong data
        w.on_check_answer()

        # Second wrong attempt triggers autocorrect
        fill_answers(w, hit=True,
                     tag=fmtb(tag, w.cache.tag_bits),
                     block_idx=fmtb(bi, w.cache.block_index_bits),
                     block_off=fmtb(bo, w.cache.block_offset_bits),
                     byte_off=fmtb(byo, w.cache.byte_offset_bits))
        fill_cache_slot(w, bi, 1, tag, 999)  # still wrong
        w.on_check_answer()

        # Memory should remain unchanged (write-back hit)
        assert w.memory.read(0x0000) == 10


class TestBugFixSetAssociativeHighlight:
    """Bug: update_all_displays always passed highlighted_way=0 in
       set-associative mode, visually steering students to Way 0."""

    def test_set_associative_highlights_all_ways(self, qapp):
        """When no specific way is known, the entire set should be highlighted."""
        cv = CacheView()
        cv.associativity = 2
        cv.num_sets = 2
        cv.tag_bits = 6
        cv.highlighted_set = 0
        cv.highlighted_way = None  # No specific way known

        # Simulate a 2-way table
        num_cols = 1 + 2 * 3  # Set + V0,Tag0,Data0 + V1,Tag1,Data1
        cv.table.setRowCount(2)
        cv.table.setColumnCount(num_cols)
        from PyQt6.QtWidgets import QTableWidgetItem
        for row in range(2):
            for col in range(num_cols):
                cv.table.setItem(row, col, QTableWidgetItem("0"))

        cv._update_set_associative(
            {0: {'ways': [{'valid': False, 'tag': 0, 'data': [0]},
                          {'valid': False, 'tag': 0, 'data': [0]}]},
             1: {'ways': [{'valid': False, 'tag': 0, 'data': [0]},
                          {'valid': False, 'tag': 0, 'data': [0]}]}},
            2
        )

        # Both ways of set 0 should be highlighted (columns 1-6)
        from PyQt6.QtGui import QColor
        display_row = 1  # set 0 is at the bottom row (num_sets - 1 - 0 = 1)
        for col in range(1, 7):  # all way columns
            item = cv.table.item(display_row, col)
            assert item is not None
            bg = item.background()
            assert bg.color() == QColor(255, 255, 150)

        # Set 1 (row 0) should NOT be highlighted
        item_s1 = cv.table.item(0, 1)
        assert item_s1 is not None
        assert item_s1.background().color() != QColor(255, 255, 150)


class TestBugFixStatsDisplay:
    """Bug: Stats showed 'Operation: N / 0' in procedural mode."""

    def test_procedural_stats_shows_problem_number(self, window):
        w = window
        w.stats_panel.update_stats(0, 0, 5, 0)
        text = w.stats_panel.operation_label.text()
        assert "Problem" in text
        assert "#5" in text
        # Should NOT contain "/ 0"
        assert "/ 0" not in text

    def test_exercise_stats_shows_operation_fraction(self, window):
        w = window
        w.stats_panel.update_stats(1, 2, 3, 10)
        text = w.stats_panel.operation_label.text()
        assert "3 / 10" in text


class TestBugFixDefaultConfig:
    """Bug: default cache size was 256 - overwhelming for beginners."""

    def test_default_cache_size_is_small(self, qapp):
        """Config panel should default to a small, beginner-friendly cache."""
        cp = ConfigPanel()
        size = cp.cache_size_combo.currentText()
        assert int(size) <= 16, f"Default cache size should be <= 16, got {size}"
