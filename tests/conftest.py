"""Shared test fixtures for the Cache Learning Application test suite."""

import sys
import os
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory_simulator import MemorySimulator
from cache_simulator import CacheSimulator
from exercise_manager import ExerciseManager, ExerciseOperation


# ---------------------------------------------------------------------------
# Model-layer fixtures (no Qt dependency)
# ---------------------------------------------------------------------------

@pytest.fixture
def memory():
    """Fresh 64KB memory simulator."""
    return MemorySimulator()


@pytest.fixture
def memory_with_data(memory):
    """Memory with some known values written."""
    memory.write(0x0000, 42)
    memory.write(0x0100, 100)
    memory.write(0x1000, 200)
    memory.write(0xFFFC, 255)
    return memory


@pytest.fixture
def direct_mapped_wt(memory):
    """Default direct-mapped, write-through cache (256 slots, 1-word blocks)."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=1,
        associativity=1,
        write_policy='write-through',
        memory_simulator=memory,
    )


@pytest.fixture
def direct_mapped_wb(memory):
    """Direct-mapped, write-back cache."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=1,
        associativity=1,
        write_policy='write-back',
        memory_simulator=memory,
    )


@pytest.fixture
def two_way_wt(memory):
    """2-way set-associative, write-through cache."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=1,
        associativity=2,
        write_policy='write-through',
        memory_simulator=memory,
    )


@pytest.fixture
def two_way_wb(memory):
    """2-way set-associative, write-back cache."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=1,
        associativity=2,
        write_policy='write-back',
        memory_simulator=memory,
    )


@pytest.fixture
def four_way_wt(memory):
    """4-way set-associative, write-through cache."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=1,
        associativity=4,
        write_policy='write-through',
        memory_simulator=memory,
    )


@pytest.fixture
def block_cache(memory):
    """Direct-mapped cache with 4-word blocks."""
    return CacheSimulator(
        cache_size_slots=256,
        block_size_words=4,
        associativity=1,
        write_policy='write-through',
        memory_simulator=memory,
    )


@pytest.fixture
def exercise_mgr(direct_mapped_wt, memory):
    """Exercise manager backed by the default direct-mapped cache."""
    return ExerciseManager(direct_mapped_wt, memory)
