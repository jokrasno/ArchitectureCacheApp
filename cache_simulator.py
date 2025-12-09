"""Cache Simulator - direct-mapped and N-way set-associative caches"""

import math
from typing import Tuple, List, Optional


class CacheEntry:
    def __init__(self, block_size_words=1):
        self.valid = False
        self.tag = 0
        self.data = [0] * block_size_words
        self.dirty = False
        self.use_bit = 0
        self.block_start_address = 0


class CacheSimulator:
    def __init__(self, cache_size_slots=256, block_size_words=1, associativity=1, 
                 write_policy='write-through', memory_simulator=None):
        self.cache_size_slots = cache_size_slots
        self.block_size_words = block_size_words
        self.associativity = associativity
        self.write_policy = write_policy
        self.memory = memory_simulator
        
        self.total_address_bits = 16
        self.bytes_per_word = 4
        self.byte_offset_bits = int(math.log2(self.bytes_per_word))
        self.block_offset_bits = int(math.log2(block_size_words)) if block_size_words > 1 else 0
        self.block_index_bits = int(math.log2(cache_size_slots))
        self.tag_bits = self.total_address_bits - self.block_index_bits - self.block_offset_bits - self.byte_offset_bits
        
        self.cache = {}
        self._initialize_cache()
        self.hits = 0
        self.misses = 0

    def _initialize_cache(self):
        if self.associativity == 1:
            for i in range(self.cache_size_slots):
                self.cache[i] = CacheEntry(self.block_size_words)
        else:
            for i in range(self.cache_size_slots):
                self.cache[i] = [CacheEntry(self.block_size_words) for _ in range(self.associativity)]

    def calculate_address_components(self, address: int) -> Tuple[int, int, int, int]:
        byte_offset = address & ((1 << self.byte_offset_bits) - 1)
        address >>= self.byte_offset_bits
        
        block_offset = address & ((1 << self.block_offset_bits) - 1) if self.block_offset_bits > 0 else 0
        address >>= self.block_offset_bits
        
        block_index = address & ((1 << self.block_index_bits) - 1)
        address >>= self.block_index_bits
        
        tag = address & ((1 << self.tag_bits) - 1)
        return tag, block_index, block_offset, byte_offset

    def _get_block_start_address(self, address: int) -> int:
        shift = self.byte_offset_bits + self.block_offset_bits
        return (address >> shift) << shift

    def _find_entry_in_set(self, set_index: int, tag: int) -> Optional[CacheEntry]:
        if self.associativity == 1:
            entry = self.cache[set_index]
            return entry if entry.valid and entry.tag == tag else None
        for entry in self.cache[set_index]:
            if entry.valid and entry.tag == tag:
                return entry
        return None

    def _select_victim_entry(self, set_index: int) -> CacheEntry:
        if self.associativity == 1:
            return self.cache[set_index]
        entries = self.cache[set_index]
        victim = entries[0]
        for entry in entries:
            if not entry.valid:
                return entry
            if entry.use_bit < victim.use_bit:
                victim = entry
        return victim

    def _update_lru(self, set_index: int, accessed_entry: CacheEntry):
        if self.associativity > 1:
            max_use = max((e.use_bit for e in self.cache[set_index] if e.valid), default=0)
            accessed_entry.use_bit = max_use + 1

    def _load_block_from_memory(self, block_start_address: int) -> List[int]:
        if self.memory:
            return self.memory.read_block(block_start_address, self.block_size_words)
        return [0] * self.block_size_words

    def _write_back_if_needed(self, entry: CacheEntry):
        if self.write_policy == 'write-back' and entry.dirty and self.memory:
            self.memory.write_block(entry.block_start_address, entry.data)
            entry.dirty = False

    def read(self, address: int) -> Tuple[bool, int, dict]:
        tag, block_index, block_offset, byte_offset = self.calculate_address_components(address)
        block_start = self._get_block_start_address(address)
        
        entry = self._find_entry_in_set(block_index, tag)
        if entry:
            self.hits += 1
            self._update_lru(block_index, entry)
            return True, entry.data[block_offset], {'hit': True, 'set_index': block_index}
        
        self.misses += 1
        block_data = self._load_block_from_memory(block_start)
        victim = self._select_victim_entry(block_index)
        
        if victim.valid:
            self._write_back_if_needed(victim)
        
        victim.valid = True
        victim.tag = tag
        victim.data = block_data.copy()
        victim.dirty = False
        victim.block_start_address = block_start
        self._update_lru(block_index, victim)
        
        return False, block_data[block_offset], {'hit': False, 'set_index': block_index}

    def _get_way_index(self, set_index: int, entry: CacheEntry) -> int:
        if self.associativity == 1:
            return 0
        for i, e in enumerate(self.cache[set_index]):
            if e is entry:
                return i
        return 0

    def write(self, address: int, value: int) -> Tuple[bool, dict]:
        tag, block_index, block_offset, byte_offset = self.calculate_address_components(address)
        block_start = self._get_block_start_address(address)
        
        entry = self._find_entry_in_set(block_index, tag)
        if entry:
            self.hits += 1
            entry.data[block_offset] = value
            if self.write_policy == 'write-back':
                entry.dirty = True
            elif self.memory:
                self.memory.write(address, value)
            self._update_lru(block_index, entry)
            return True, {'hit': True, 'set_index': block_index}
        
        self.misses += 1
        if self.write_policy == 'write-through':
            if self.memory:
                self.memory.write(address, value)
        else:
            block_data = self._load_block_from_memory(block_start)
            block_data[block_offset] = value
            victim = self._select_victim_entry(block_index)
            if victim.valid:
                self._write_back_if_needed(victim)
            victim.valid = True
            victim.tag = tag
            victim.data = block_data
            victim.dirty = True
            victim.block_start_address = block_start
            self._update_lru(block_index, victim)
        
        return False, {'hit': False, 'set_index': block_index}

    def get_cache_state(self) -> dict:
        state = {}
        for set_idx in range(self.cache_size_slots):
            if self.associativity == 1:
                entry = self.cache[set_idx]
                state[set_idx] = {'ways': [{'valid': entry.valid, 'tag': entry.tag, 
                                           'data': entry.data.copy(), 'dirty': entry.dirty}]}
            else:
                state[set_idx] = {'ways': [{'valid': e.valid, 'tag': e.tag, 
                                           'data': e.data.copy(), 'dirty': e.dirty} 
                                          for e in self.cache[set_idx]]}
        return state

    def reset(self):
        self._initialize_cache()
        self.hits = 0
        self.misses = 0

    def get_statistics(self) -> dict:
        total = self.hits + self.misses
        return {'hits': self.hits, 'misses': self.misses, 'total': total,
                'hit_rate': (self.hits / total * 100) if total > 0 else 0}
