"""Memory Simulator - 64K byte memory with 16-bit addresses"""


class MemorySimulator:
    def __init__(self, size_kb=64):
        self.size_bytes = size_kb * 1024
        self.words_per_address = 4
        self.memory = {}
        self.modified_addresses = set()
        self._initialize_default()

    def _initialize_default(self):
        for addr in range(0, self.size_bytes, self.words_per_address):
            self.memory[addr] = 0

    def initialize_custom(self, address_value_pairs):
        if isinstance(address_value_pairs, dict):
            for addr, value in address_value_pairs.items():
                self.write(addr, value)
        else:
            for addr, value in address_value_pairs:
                self.write(addr, value)

    def read(self, address):
        address = (address // self.words_per_address) * self.words_per_address
        return self.memory.get(address, 0)

    def read_block(self, start_address, block_size_words):
        start_address = (start_address // self.words_per_address) * self.words_per_address
        return [self.read(start_address + i * self.words_per_address) for i in range(block_size_words)]

    def write(self, address, value):
        address = (address // self.words_per_address) * self.words_per_address
        self.memory[address] = value
        self.modified_addresses.add(address)

    def write_block(self, start_address, block_data):
        start_address = (start_address // self.words_per_address) * self.words_per_address
        for i, value in enumerate(block_data):
            self.write(start_address + i * self.words_per_address, value)

    def reset(self):
        self.memory.clear()
        self.modified_addresses.clear()
        self._initialize_default()

    def get_all_addresses(self):
        return sorted(self.memory.keys())

    def get_relevant_addresses(self, additional_addresses=None):
        """Return non-zero addresses plus any additional addresses of interest."""
        addresses = {addr for addr, value in self.memory.items() if value != 0}
        if additional_addresses:
            addresses.update(additional_addresses)
        return sorted(addresses)
