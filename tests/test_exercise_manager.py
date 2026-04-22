"""Tests for ExerciseManager — operation tracking, validation, procedural mode."""

import pytest
from unittest.mock import MagicMock
from exercise_manager import ExerciseManager, ExerciseOperation
from memory_simulator import MemorySimulator
from cache_simulator import CacheSimulator


# Helper to create a fresh exercise manager with real simulators
def make_mgr(cache_size=256, associativity=1, write_policy='write-through'):
    mem = MemorySimulator()
    cache = CacheSimulator(
        cache_size_slots=cache_size,
        associativity=associativity,
        write_policy=write_policy,
        memory_simulator=mem,
    )
    return ExerciseManager(cache, mem), cache, mem


# ===========================================================================
# Operation navigation
# ===========================================================================

class TestNavigation:

    def test_load_exercise_resets(self):
        mgr, _, _ = make_mgr()
        ops = [ExerciseOperation('read', 0x0000), ExerciseOperation('write', 0x0004, 42)]
        mgr.load_exercise(ops)
        assert mgr.get_operation_number() == 1
        assert mgr.get_total_operations() == 2

    def test_next_and_previous(self):
        mgr, _, _ = make_mgr()
        ops = [ExerciseOperation('read', 0x0000),
               ExerciseOperation('read', 0x0004),
               ExerciseOperation('read', 0x0008)]
        mgr.load_exercise(ops)
        assert mgr.get_operation_number() == 1
        mgr.next_operation()
        assert mgr.get_operation_number() == 2
        mgr.next_operation()
        assert mgr.get_operation_number() == 3
        mgr.previous_operation()
        assert mgr.get_operation_number() == 2

    def test_next_at_end_stays(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        mgr.next_operation()  # no-op, only 1 op
        assert mgr.get_operation_number() == 1

    def test_previous_at_start_stays(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        mgr.previous_operation()  # no-op
        assert mgr.get_operation_number() == 1

    def test_has_next_has_previous(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([
            ExerciseOperation('read', 0x0000),
            ExerciseOperation('read', 0x0004),
        ])
        assert mgr.has_next() is True
        assert mgr.has_previous() is False
        mgr.next_operation()
        assert mgr.has_next() is False
        assert mgr.has_previous() is True

    def test_get_current_operation_none_when_empty(self):
        mgr, _, _ = make_mgr()
        assert mgr.get_current_operation() is None


# ===========================================================================
# Hit/Miss validation
# ===========================================================================

class TestValidateHitMiss:

    def test_correct_hit(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        is_correct, should_advance, msg = mgr.validate_hit_miss(True, actual_hit=True)
        assert is_correct is True

    def test_correct_miss(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        is_correct, _, _ = mgr.validate_hit_miss(False, actual_hit=False)
        assert is_correct is True

    def test_wrong_answer_increments_attempts(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        is_correct, should_advance, _ = mgr.validate_hit_miss(True, actual_hit=False)
        assert is_correct is False
        assert should_advance is False  # still have 1 attempt left

    def test_max_attempts_auto_advances(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        mgr.validate_hit_miss(True, actual_hit=False)   # attempt 1
        is_correct, should_advance, msg = mgr.validate_hit_miss(True, actual_hit=False)  # attempt 2
        assert is_correct is False
        assert should_advance is True  # max attempts reached

    def test_correct_answer_resets_attempts(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        mgr.validate_hit_miss(True, actual_hit=False)  # wrong
        mgr.validate_hit_miss(False, actual_hit=False)  # correct
        assert mgr.get_attempts_for_current() == 0


# ===========================================================================
# Address decomposition validation
# ===========================================================================

class TestValidateAddressDecomposition:

    def test_correct_decomposition(self):
        mgr, cache, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x1234)])
        tag, bi, bo, byo = cache.calculate_address_components(0x1234)
        is_correct, _, _ = mgr.validate_address_decomposition(tag, bi, byo, bo)
        assert is_correct is True

    def test_wrong_tag(self):
        mgr, cache, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x1234)])
        tag, bi, bo, byo = cache.calculate_address_components(0x1234)
        is_correct, _, msg = mgr.validate_address_decomposition(tag + 1, bi, byo, bo)
        assert is_correct is False
        assert "Tag" in msg

    def test_wrong_block_index(self):
        mgr, cache, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x1234)])
        tag, bi, bo, byo = cache.calculate_address_components(0x1234)
        is_correct, _, msg = mgr.validate_address_decomposition(tag, bi + 1, byo, bo)
        assert is_correct is False
        assert "BI" in msg

    def test_no_current_operation(self):
        mgr, _, _ = make_mgr()
        is_correct, _, msg = mgr.validate_address_decomposition(0, 0, 0, 0)
        assert is_correct is False
        assert "No current operation" in msg


# ===========================================================================
# Execute operations
# ===========================================================================

class TestExecuteOperations:

    def test_execute_read(self):
        mgr, cache, mem = make_mgr()
        mem.write(0x0000, 42)
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        hit, value, state = mgr.execute_current_operation()
        assert hit is False  # first read
        assert value == 42

    def test_execute_write(self):
        mgr, cache, mem = make_mgr()
        mgr.load_exercise([ExerciseOperation('write', 0x0000, 99)])
        hit, value, state = mgr.execute_current_operation()
        assert hit is False  # first write to this address
        assert value is None  # writes return None for value
        assert mem.read(0x0000) == 99

    def test_execute_no_operation(self):
        mgr, _, _ = make_mgr()
        hit, value, state = mgr.execute_current_operation()
        assert hit is False
        assert value is None


# ===========================================================================
# Procedural mode
# ===========================================================================

class TestProceduralMode:

    def test_generate_random_operation(self):
        mgr, cache, mem = make_mgr()
        mem.write(0x0000, 42)
        op = mgr.generate_random_operation()
        assert op.operation_type in ('read', 'write')
        assert op.address % 4 == 0  # word-aligned

    def test_set_procedural_operation(self):
        mgr, _, _ = make_mgr()
        op = ExerciseOperation('read', 0x1234)
        mgr.set_procedural_operation(op)
        assert mgr.get_current_operation() == op
        assert mgr.get_total_operations() == 1
        assert mgr.current_answered_correctly is False

    def test_generate_then_check(self):
        """Full procedural cycle: generate → simulate student → execute."""
        mgr, cache, mem = make_mgr()
        mem.write(0x0000, 42)
        op = ExerciseOperation('read', 0x0000)
        mgr.set_procedural_operation(op)

        tag, bi, bo, byo = cache.calculate_address_components(0x0000)
        assert tag == 0
        assert bi == 0

        # Execute the operation
        hit, value, _ = mgr.execute_current_operation()
        assert hit is False  # first access
        assert value == 42

    def test_generate_write_operation(self):
        mgr, _, mem = make_mgr()
        mem.write(0x0000, 42)
        op = ExerciseOperation('write', 0x0000, 99)
        mgr.set_procedural_operation(op)
        mgr.execute_current_operation()
        assert mem.read(0x0000) == 99


# ===========================================================================
# Reset
# ===========================================================================

class TestReset:

    def test_reset_to_beginning(self):
        mgr, _, _ = make_mgr()
        ops = [ExerciseOperation('read', 0x0000),
               ExerciseOperation('read', 0x0004)]
        mgr.load_exercise(ops)
        mgr.next_operation()
        assert mgr.get_operation_number() == 2
        mgr.reset_to_beginning()
        assert mgr.get_operation_number() == 1
        assert mgr.current_answered_correctly is False
        assert len(mgr.attempts_per_question) == 0

    def test_mark_current_answered(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        assert mgr.is_current_answered() is False
        mgr.mark_current_answered()
        assert mgr.is_current_answered() is True


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:

    def test_load_empty_operations(self):
        mgr, _, _ = make_mgr()
        mgr.load_exercise([])
        assert mgr.get_current_operation() is None
        assert mgr.get_total_operations() == 0

    def test_get_correct_decomposition_no_op(self):
        mgr, _, _ = make_mgr()
        result = mgr.get_correct_address_decomposition()
        assert result == (0, 0, 0, 0)

    def test_procedural_with_empty_memory(self):
        """Procedural mode should still work with all-zero memory."""
        mgr, _, _ = make_mgr()
        op = mgr.generate_random_operation()
        assert op is not None

    def test_exercise_with_set_associative(self):
        mgr, cache, mem = make_mgr(cache_size=256, associativity=2)
        mem.write(0x0000, 42)
        mgr.load_exercise([ExerciseOperation('read', 0x0000)])
        hit, value, _ = mgr.execute_current_operation()
        assert hit is False
        assert value == 42
