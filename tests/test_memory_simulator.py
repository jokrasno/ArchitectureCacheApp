"""Tests for MemorySimulator."""

import pytest
from memory_simulator import MemorySimulator


class TestBasicReadWrite:

    def test_read_uninitialized_returns_zero(self, memory):
        assert memory.read(0x0000) == 0

    def test_write_and_read(self, memory):
        memory.write(0x0000, 42)
        assert memory.read(0x0000) == 42

    def test_write_overwrites(self, memory):
        memory.write(0x0000, 42)
        memory.write(0x0000, 99)
        assert memory.read(0x0000) == 99

    def test_address_alignment(self, memory):
        """Non-aligned addresses should snap to word boundary."""
        memory.write(1, 42)
        assert memory.read(0) == 42
        assert memory.read(1) == 42
        assert memory.read(2) == 42
        assert memory.read(3) == 42

    def test_different_addresses_independent(self, memory):
        memory.write(0x0000, 10)
        memory.write(0x0004, 20)
        assert memory.read(0x0000) == 10
        assert memory.read(0x0004) == 20


class TestBlockOperations:

    def test_read_block(self, memory):
        memory.write(0x0000, 10)
        memory.write(0x0004, 20)
        memory.write(0x0008, 30)
        block = memory.read_block(0x0000, 3)
        assert block == [10, 20, 30]

    def test_read_block_uninitialized(self, memory):
        block = memory.read_block(0x8000, 4)
        assert block == [0, 0, 0, 0]

    def test_write_block(self, memory):
        memory.write_block(0x0000, [10, 20, 30])
        assert memory.read(0x0000) == 10
        assert memory.read(0x0004) == 20
        assert memory.read(0x0008) == 30

    def test_read_block_start_alignment(self, memory):
        memory.write(0x0004, 50)
        block = memory.read_block(0x0001, 2)  # start_address 1 aligns to 0
        assert block[0] == 0  # addr 0x0000
        assert block[1] == 50  # addr 0x0004


class TestModifiedAddresses:

    def test_write_tracks_modified(self, memory):
        memory.write(0x0000, 42)
        assert 0x0000 in memory.modified_addresses

    def test_modified_across_multiple_writes(self, memory):
        memory.write(0x0000, 1)
        memory.write(0x0100, 2)
        assert 0x0000 in memory.modified_addresses
        assert 0x0100 in memory.modified_addresses


class TestReset:

    def test_reset_clears_values(self, memory):
        memory.write(0x0000, 42)
        memory.reset()
        assert memory.read(0x0000) == 0

    def test_reset_clears_modified(self, memory):
        memory.write(0x0000, 42)
        memory.reset()
        assert len(memory.modified_addresses) == 0

    def test_reset_restores_full_address_space(self, memory):
        memory.reset()
        assert len(memory.get_all_addresses()) == 65536 // 4


class TestGetRelevantAddresses:

    def test_filters_zeros(self, memory):
        memory.write(0x0000, 42)
        memory.write(0x0004, 0)  # zero — should not appear
        memory.write(0x0008, 99)
        addrs = memory.get_relevant_addresses()
        assert 0x0000 in addrs
        assert 0x0008 in addrs
        # 0x0004 should NOT be in relevant addresses (value is 0)
        # But note: _initialize_default sets all to 0, and writing 0 keeps it 0
        # So 0x0004 won't appear since its value is 0

    def test_includes_additional_addresses(self, memory):
        memory.write(0x0000, 42)
        addrs = memory.get_relevant_addresses(additional_addresses={0x8000})
        assert 0x0000 in addrs
        assert 0x8000 in addrs  # included even though value is 0

    def test_empty_memory_with_no_additional(self, memory):
        addrs = memory.get_relevant_addresses()
        # Fresh memory has all zeros, so no relevant addresses
        assert len(addrs) == 0


class TestGetAllAddresses:

    def test_returns_all_16k_addresses(self, memory):
        addrs = memory.get_all_addresses()
        assert len(addrs) == 16384

    def test_addresses_are_sorted(self, memory):
        addrs = memory.get_all_addresses()
        assert addrs == sorted(addrs)

    def test_addresses_are_word_aligned(self, memory):
        addrs = memory.get_all_addresses()
        for a in addrs:
            assert a % 4 == 0


class TestInitializeCustom:

    def test_from_dict(self, memory):
        memory.initialize_custom({0x0000: 10, 0x0004: 20})
        assert memory.read(0x0000) == 10
        assert memory.read(0x0004) == 20

    def test_from_list_of_tuples(self, memory):
        memory.initialize_custom([(0x0000, 10), (0x0004, 20)])
        assert memory.read(0x0000) == 10
        assert memory.read(0x0004) == 20
