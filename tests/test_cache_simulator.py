"""Tests for CacheSimulator — core cache logic."""

import pytest
from cache_simulator import CacheSimulator, CacheEntry
from memory_simulator import MemorySimulator


# ===========================================================================
# Address decomposition
# ===========================================================================

class TestAddressDecomposition:
    """Verify that calculate_address_components splits addresses correctly."""

    def test_zero_address(self, direct_mapped_wt):
        tag, bi, bo, byo = direct_mapped_wt.calculate_address_components(0x0000)
        assert tag == 0
        assert bi == 0
        assert bo == 0
        assert byo == 0

    def test_max_address(self, direct_mapped_wt):
        # 0xFFFC = last word-aligned address in 16-bit space
        tag, bi, bo, byo = direct_mapped_wt.calculate_address_components(0xFFFC)
        assert byo == 0  # word-aligned → byte offset 0

    def test_round_trip(self, direct_mapped_wt):
        """Decomposing and rebuilding the block-index bits should be consistent."""
        addr = 0x1234
        tag, bi, bo, byo = direct_mapped_wt.calculate_address_components(addr)
        # bi is (addr >> 2) & 0xFF for 256-slot cache
        expected_bi = (addr >> 2) & 0xFF
        assert bi == expected_bi

    def test_block_offset_with_multiword_blocks(self, block_cache):
        addr = 0x0010  # block_offset should be non-zero for 4-word blocks
        tag, bi, bo, byo = block_cache.calculate_address_components(addr)
        # With 4-word blocks: byte_offset=2 bits, block_offset=2 bits
        # addr=0x0010 = 0b000000010000
        # byte_offset = addr & 0x3 = 0
        # then >>2: 0b0000000100 → block_offset = 0b00 = 0
        # Actually let me compute: 0x0010 = 16 decimal
        # byte_offset = 16 & 3 = 0
        # after >>2: 4. block_offset = 4 & 3 = 0. After >>2: 1. bi = 1 & 0xFF = 1.
        assert bo == 0

    def test_nonzero_block_offset(self, block_cache):
        addr = 0x001C  # 28 decimal
        # byte_offset = 28 & 3 = 0
        # >>2 → 7. block_offset = 7 & 3 = 3
        tag, bi, bo, byo = block_cache.calculate_address_components(addr)
        assert bo == 3
        assert byo == 0


# ===========================================================================
# Read operations
# ===========================================================================

class TestReadOperations:

    def test_first_read_is_miss(self, direct_mapped_wt):
        hit, value, info = direct_mapped_wt.read(0x0000)
        assert hit is False
        assert info['hit'] is False

    def test_second_read_same_address_is_hit(self, direct_mapped_wt):
        direct_mapped_wt.read(0x0000)
        hit, value, info = direct_mapped_wt.read(0x0000)
        assert hit is True
        assert info['hit'] is True

    def test_read_returns_memory_value(self, direct_mapped_wt, memory):
        memory.write(0x0000, 42)
        hit, value, info = direct_mapped_wt.read(0x0000)
        assert value == 42

    def test_read_miss_loads_into_cache(self, direct_mapped_wt, memory):
        memory.write(0x0100, 99)
        direct_mapped_wt.read(0x0100)
        # Second read should be a hit
        hit, value, info = direct_mapped_wt.read(0x0100)
        assert hit is True
        assert value == 99

    def test_read_replaces_cache_entry(self, direct_mapped_wt):
        # Two addresses that map to the same slot (same block index)
        # With 256 slots: block_index = (addr >> 2) & 0xFF
        addr1 = 0x0000  # bi=0
        addr2 = 0x0400  # bi=0 (0x400 >> 2 = 0x100, & 0xFF = 0)
        direct_mapped_wt.read(addr1)
        direct_mapped_wt.read(addr2)
        # Reading addr1 again should be a miss (addr2 evicted it)
        hit, _, _ = direct_mapped_wt.read(addr1)
        assert hit is False

    def test_read_returns_zero_for_uninitialized_memory(self, direct_mapped_wt):
        hit, value, info = direct_mapped_wt.read(0x8000)
        assert value == 0


# ===========================================================================
# Write operations — write-through
# ===========================================================================

class TestWriteThrough:

    def test_write_hit_updates_memory(self, direct_mapped_wt, memory):
        direct_mapped_wt.read(0x0000)  # load into cache
        direct_mapped_wt.write(0x0000, 77)
        assert memory.read(0x0000) == 77

    def test_write_miss_updates_memory(self, direct_mapped_wt, memory):
        direct_mapped_wt.write(0x0000, 55)
        # Memory should be written (write-through)
        assert memory.read(0x0000) == 55

    def test_write_miss_no_write_allocate(self, direct_mapped_wt):
        """Write-through miss should NOT load the block into cache."""
        direct_mapped_wt.write(0x0000, 55)
        # A subsequent read should still be a miss (block wasn't allocated)
        hit, value, _ = direct_mapped_wt.read(0x0000)
        assert hit is False
        # But the read should return the value we wrote to memory
        assert value == 55

    def test_write_hit_updates_cache_data(self, direct_mapped_wt):
        direct_mapped_wt.read(0x0000)  # load into cache
        direct_mapped_wt.write(0x0000, 99)
        hit, value, _ = direct_mapped_wt.read(0x0000)
        assert hit is True
        assert value == 99


# ===========================================================================
# Write operations — write-back
# ===========================================================================

class TestWriteBack:

    def test_write_hit_sets_dirty_bit(self, direct_mapped_wb):
        direct_mapped_wb.read(0x0000)
        direct_mapped_wb.write(0x0000, 42)
        state = direct_mapped_wb.get_cache_state()
        assert state[0]['ways'][0]['dirty'] is True

    def test_write_hit_does_not_update_memory(self, direct_mapped_wb, memory):
        direct_mapped_wb.read(0x0000)
        direct_mapped_wb.write(0x0000, 42)
        # Memory should NOT be updated yet (write-back)
        assert memory.read(0x0000) == 0

    def test_write_back_on_eviction(self, direct_mapped_wb, memory):
        # Two addresses that map to the same slot
        addr1 = 0x0000  # bi=0
        addr2 = 0x0400  # bi=0
        direct_mapped_wb.read(addr1)
        direct_mapped_wb.write(addr1, 42)
        # addr1 is now dirty. Evict it by reading addr2
        direct_mapped_wb.read(addr2)
        # Memory should now have the written value
        assert memory.read(addr1) == 42

    def test_write_back_miss_allocates(self, direct_mapped_wb, memory):
        """Write-back miss should allocate the block (write-allocate)."""
        direct_mapped_wb.write(0x0000, 42)
        # Block should be in cache now (write-allocate)
        hit, value, _ = direct_mapped_wb.read(0x0000)
        assert hit is True
        assert value == 42
        # Memory should NOT be updated yet
        assert memory.read(0x0000) == 0

    def test_write_back_miss_sets_dirty(self, direct_mapped_wb):
        direct_mapped_wb.write(0x0000, 42)
        # Check that the entry is dirty
        state = direct_mapped_wb.get_cache_state()
        assert state[0]['ways'][0]['dirty'] is True


# ===========================================================================
# Set-associative cache
# ===========================================================================

class TestSetAssociative:

    def test_two_ways_hold_two_tags(self, two_way_wt):
        """Two different tags mapping to the same set should both hit."""
        # 256 sets, block_index_bits=8, mask=0xFF
        addr1 = 0x0000  # bi=0
        addr2 = 0x0400  # bi=0 (0x400>>2=0x100, &0xFF=0), different tag
        two_way_wt.read(addr1)
        two_way_wt.read(addr2)
        # Both should be in cache now
        hit1, _, _ = two_way_wt.read(addr1)
        hit2, _, _ = two_way_wt.read(addr2)
        assert hit1 is True
        assert hit2 is True

    def test_lru_eviction(self, two_way_wt):
        """Third unique tag in same set should evict the LRU entry."""
        addr1 = 0x0000
        addr2 = 0x0400  # same set as addr1 (bi=0)
        addr3 = 0x0800  # same set as addr1 (bi=0)
        two_way_wt.read(addr1)
        two_way_wt.read(addr2)
        # Access addr1 again to make addr2 the LRU
        two_way_wt.read(addr1)
        # Now read addr3 — should evict addr2 (LRU)
        two_way_wt.read(addr3)
        # Verify via cache state (not reads, which cause more evictions)
        state = two_way_wt.get_cache_state()
        ways = state[0]['ways']
        tags = {way['tag'] for way in ways if way['valid']}
        tag1 = two_way_wt.calculate_address_components(addr1)[0]
        tag2 = two_way_wt.calculate_address_components(addr2)[0]
        tag3 = two_way_wt.calculate_address_components(addr3)[0]
        assert tag1 in tags   # addr1 still present
        assert tag2 not in tags  # addr2 evicted (was LRU)
        assert tag3 in tags   # addr3 newly loaded

    def test_four_way_capacity(self, four_way_wt):
        """4-way cache should hold 4 different tags in same set."""
        base = 0x0000
        addrs = [base + i * 0x0800 for i in range(4)]  # all map to same set
        for a in addrs:
            four_way_wt.read(a)
        for a in addrs:
            hit, _, _ = four_way_wt.read(a)
            assert hit is True

    def test_write_back_set_associative_eviction(self, two_way_wb, memory):
        """Dirty write-back entry should flush to memory on eviction."""
        addr1 = 0x0000
        addr2 = 0x0400  # same set (bi=0)
        addr3 = 0x0800  # same set (bi=0)
        two_way_wb.read(addr1)
        two_way_wb.write(addr1, 42)
        two_way_wb.read(addr2)  # fill way 1
        # Access addr2 to make addr1 LRU
        two_way_wb.read(addr2)
        # Evict addr1 by reading addr3
        two_way_wb.read(addr3)
        assert memory.read(addr1) == 42

    def test_get_cache_state_set_associative(self, two_way_wt):
        state = two_way_wt.get_cache_state()
        assert len(state) == 256  # cache_size_slots=256 sets
        for set_idx, set_data in state.items():
            assert 'ways' in set_data
            assert len(set_data['ways']) == 2


# ===========================================================================
# Multi-word blocks
# ===========================================================================

class TestMultiWordBlocks:

    def test_block_read_loads_all_words(self, block_cache, memory):
        memory.write(0x0000, 10)
        memory.write(0x0004, 20)
        memory.write(0x0008, 30)
        memory.write(0x000C, 40)
        block_cache.read(0x0000)
        # All words in the block should be in cache
        for addr, expected in [(0x0000, 10), (0x0004, 20), (0x0008, 30), (0x000C, 40)]:
            hit, value, _ = block_cache.read(addr)
            assert hit is True
            assert value == expected

    def test_block_write_updates_correct_word(self, block_cache, memory):
        memory.write(0x0000, 10)
        memory.write(0x0004, 20)
        block_cache.read(0x0000)  # load block
        block_cache.write(0x0004, 99)  # write-through updates memory
        assert memory.read(0x0004) == 99


# ===========================================================================
# Statistics
# ===========================================================================

class TestStatistics:

    def test_initial_stats(self, direct_mapped_wt):
        stats = direct_mapped_wt.get_statistics()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['total'] == 0
        assert stats['hit_rate'] == 0

    def test_hit_rate_calculation(self, direct_mapped_wt):
        direct_mapped_wt.read(0x0000)  # miss
        direct_mapped_wt.read(0x0000)  # hit
        direct_mapped_wt.read(0x0000)  # hit
        stats = direct_mapped_wt.get_statistics()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == pytest.approx(200/3, rel=1e-6)

    def test_reset_clears_stats(self, direct_mapped_wt):
        direct_mapped_wt.read(0x0000)
        direct_mapped_wt.read(0x0000)
        direct_mapped_wt.reset()
        stats = direct_mapped_wt.get_statistics()
        assert stats['hits'] == 0
        assert stats['misses'] == 0


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:

    def test_address_zero(self, direct_mapped_wt):
        hit, value, info = direct_mapped_wt.read(0)
        assert hit is False
        assert info['set_index'] == 0

    def test_max_word_aligned_address(self, direct_mapped_wt):
        hit, value, info = direct_mapped_wt.read(0xFFFC)
        assert hit is False

    def test_non_aligned_address_gets_aligned(self, direct_mapped_wt, memory):
        """Writing to a non-word-aligned address should align it."""
        memory.write(1, 42)  # address 1 aligns to 0
        assert memory.read(0) == 42
        assert memory.read(1) == 42  # reads also align

    def test_small_cache_2_slots(self, memory):
        cache = CacheSimulator(cache_size_slots=2, memory_simulator=memory)
        hit, _, _ = cache.read(0x0000)  # bi=0
        assert hit is False
        hit, _, _ = cache.read(0x0004)  # bi=1
        assert hit is False
        hit, _, _ = cache.read(0x0000)  # bi=0, should still be there
        assert hit is True

    def test_cache_state_reflects_operations(self, direct_mapped_wt, memory):
        memory.write(0x0000, 42)
        direct_mapped_wt.read(0x0000)
        state = direct_mapped_wt.get_cache_state()
        entry = state[0]['ways'][0]
        assert entry['valid'] is True
        assert entry['data'] == [42]

    def test_cache_state_copies_data(self, direct_mapped_wt):
        """get_cache_state should return copies, not references."""
        direct_mapped_wt.read(0x0000)
        state = direct_mapped_wt.get_cache_state()
        state[0]['ways'][0]['data'][0] = 999
        # Original should be unchanged
        actual_data = direct_mapped_wt.cache[0].data
        assert actual_data[0] != 999

    def test_cache_without_memory(self):
        """Cache should work even without a memory simulator (returns zeros)."""
        cache = CacheSimulator(cache_size_slots=4, memory_simulator=None)
        hit, value, _ = cache.read(0x0000)
        assert hit is False
        assert value == 0
