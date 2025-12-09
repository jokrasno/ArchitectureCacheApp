"""Exercise Manager - manages questions, attempts, and progression"""

from typing import List, Tuple, Optional
import random


class ExerciseOperation:
    def __init__(self, operation_type: str, address: int, value: Optional[int] = None):
        self.operation_type = operation_type
        self.address = address
        self.value = value


class ExerciseManager:
    def __init__(self, cache_simulator, memory_simulator):
        self.cache = cache_simulator
        self.memory = memory_simulator
        self.operations: List[ExerciseOperation] = []
        self.current_operation_index = 0
        self.attempts_per_question = {}
        self.max_attempts = 2
        self.current_answered_correctly = False

    def load_exercise(self, operations: List[ExerciseOperation], reset_cache=True):
        self.operations = operations
        self.current_operation_index = 0
        self.attempts_per_question = {}
        self.current_answered_correctly = False
        if reset_cache:
            self.cache.reset()
            # Don't reset memory here - it's already been populated by the exercise loader

    def get_current_operation(self) -> Optional[ExerciseOperation]:
        if 0 <= self.current_operation_index < len(self.operations):
            return self.operations[self.current_operation_index]
        return None

    def get_operation_number(self) -> int:
        return self.current_operation_index + 1

    def get_total_operations(self) -> int:
        return len(self.operations)

    def has_next(self) -> bool:
        return self.current_operation_index < len(self.operations) - 1

    def has_previous(self) -> bool:
        return self.current_operation_index > 0

    def next_operation(self):
        if self.has_next():
            self.current_operation_index += 1
            self.current_answered_correctly = False

    def previous_operation(self):
        if self.has_previous():
            self.current_operation_index -= 1
            self.current_answered_correctly = False

    def mark_current_answered(self):
        self.current_answered_correctly = True

    def is_current_answered(self) -> bool:
        return self.current_answered_correctly

    def get_attempts_for_current(self) -> int:
        return self.attempts_per_question.get(self.current_operation_index, 0)

    def validate_hit_miss(self, student_answer: bool, actual_hit: bool = None) -> Tuple[bool, bool, str]:
        op = self.get_current_operation()
        if not op:
            return False, False, "No current operation"
        
        is_correct = actual_hit == student_answer
        attempts = self.get_attempts_for_current()
        
        if is_correct:
            self.attempts_per_question[self.current_operation_index] = 0
            return True, True, "Correct!"
        
        attempts += 1
        self.attempts_per_question[self.current_operation_index] = attempts
        
        if attempts >= self.max_attempts:
            return False, True, f"Incorrect. Answer: {'Hit' if actual_hit else 'Miss'}."
        return False, False, "Incorrect, try again."

    def validate_address_decomposition(self, tag: int, block_index: int, 
                                       byte_offset: int, block_offset: int) -> Tuple[bool, bool, str]:
        op = self.get_current_operation()
        if not op:
            return False, False, "No current operation"
        
        correct = self.cache.calculate_address_components(op.address)
        correct_tag, correct_bi, correct_bo, correct_byo = correct
        
        all_correct = (tag == correct_tag and block_index == correct_bi and 
                      byte_offset == correct_byo and block_offset == correct_bo)
        
        attempts = self.get_attempts_for_current()
        
        if all_correct:
            self.attempts_per_question[self.current_operation_index] = 0
            return True, True, "Correct!"
        
        attempts += 1
        self.attempts_per_question[self.current_operation_index] = attempts
        
        if attempts >= self.max_attempts:
            return False, True, f"Incorrect. Tag={correct_tag}, BI={correct_bi}, BO={correct_bo}, ByteO={correct_byo}"
        
        errors = []
        if tag != correct_tag: errors.append(f"Tag ({correct_tag})")
        if block_index != correct_bi: errors.append(f"BI ({correct_bi})")
        if block_offset != correct_bo: errors.append(f"BO ({correct_bo})")
        if byte_offset != correct_byo: errors.append(f"ByteO ({correct_byo})")
        return False, False, f"Wrong: {', '.join(errors)}"

    def get_correct_address_decomposition(self) -> Tuple[int, int, int, int]:
        op = self.get_current_operation()
        if not op:
            return 0, 0, 0, 0
        return self.cache.calculate_address_components(op.address)

    def reset_to_beginning(self):
        self.current_operation_index = 0
        self.attempts_per_question = {}
        self.current_answered_correctly = False
        self.cache.reset()

    def execute_current_operation(self) -> Tuple[bool, Optional[int], dict]:
        op = self.get_current_operation()
        if not op:
            return False, None, {}
        
        if op.operation_type == 'read':
            hit, value, state = self.cache.read(op.address)
            return hit, value, state
        hit, state = self.cache.write(op.address, op.value)
        return hit, None, state

    def generate_random_operation(self) -> ExerciseOperation:
        """Generate a random operation for procedural mode"""
        # Pick from addresses that have non-zero values, or random addresses
        known_addresses = [addr for addr in self.memory.get_all_addresses() 
                          if self.memory.read(addr) != 0]
        
        if known_addresses and random.random() < 0.7:
            # 70% chance to pick from known addresses (more interesting)
            address = random.choice(known_addresses)
        else:
            # 30% chance for random address
            address = random.randrange(0, 65536, 4)
        
        # 80% reads, 20% writes
        if random.random() < 0.8:
            return ExerciseOperation('read', address)
        else:
            return ExerciseOperation('write', address, random.randint(1, 1000))

    def set_procedural_operation(self, op: ExerciseOperation):
        """Set a single operation for procedural mode"""
        self.operations = [op]
        self.current_operation_index = 0
        self.current_answered_correctly = False
        self.attempts_per_question = {}
