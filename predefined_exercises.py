"""
DEPRECATED: Predefined Exercise Sequences

This module contains preset exercises that are currently disabled in the UI.
To re-enable:
1. Uncomment the import in gui/main_window.py
2. Uncomment the menu action in create_menu_bar()
3. Uncomment the on_load_exercise method
"""

from exercise_manager import ExerciseOperation


def get_part2_exercise(memory) -> list:
    """Part 2: Direct-mapped cache with 4-word blocks"""
    memory.initialize_custom({
        0x26C0: 22, 0x26C4: 33, 0x26C8: 44, 0x26CC: 55,
        0x3520: 66, 0x3524: 77, 0x3528: 88, 0x352C: 99,
        0xBD20: 4444, 0xBD24: 5555, 0xBD28: 6666, 0xBD2C: 7777,
        0x8120: 555, 0x8124: 666, 0x8128: 777, 0x812C: 888,
    })
    return [
        ExerciseOperation('read', 0xBD28),
        ExerciseOperation('read', 0xBD24),
        ExerciseOperation('read', 0x8128),
        ExerciseOperation('read', 0xBD20),
        ExerciseOperation('read', 0xBD2C),
        ExerciseOperation('read', 0x8120),
        ExerciseOperation('read', 0x8124),
        ExerciseOperation('read', 0x812C),
        ExerciseOperation('read', 0x26C0),
        ExerciseOperation('read', 0x26C4),
    ]


def get_part3_exercise(memory) -> list:
    """Part 3: 2-way set-associative cache with LRU"""
    memory.initialize_custom({
        0x3238: 123, 0x3748: 234, 0x3738: 123,
        0x9238: 345, 0x92A8: 456, 0xF038: 567, 0xF0A8: 678,
    })
    return [
        ExerciseOperation('read', 0x3738),
        ExerciseOperation('read', 0xF0A8),
        ExerciseOperation('read', 0x92A8),
        ExerciseOperation('read', 0x3238),
        ExerciseOperation('read', 0x3748),
        ExerciseOperation('read', 0x9238),
        ExerciseOperation('read', 0xF038),
        ExerciseOperation('read', 0x3738),
    ]


def get_simple_direct_mapped_exercise(memory) -> list:
    """Simple direct-mapped cache exercise"""
    memory.initialize_custom({
        0x1000: 100, 0x1004: 200, 0x1008: 300, 0x100C: 400,
        0x2000: 500, 0x2004: 600,
    })
    return [
        ExerciseOperation('read', 0x1000),
        ExerciseOperation('read', 0x1004),
        ExerciseOperation('read', 0x2000),
        ExerciseOperation('read', 0x1000),
    ]


def get_write_exercise(memory) -> list:
    """Exercise with write operations"""
    memory.initialize_custom({0x3000: 1000, 0x3004: 2000, 0x4000: 3000})
    return [
        ExerciseOperation('read', 0x3000),
        ExerciseOperation('write', 0x3004, 2500),
        ExerciseOperation('read', 0x4000),
        ExerciseOperation('read', 0x3004),
    ]


EXERCISE_REGISTRY = {
    "Part 2 - Direct-Mapped (4-word blocks)": get_part2_exercise,
    "Part 3 - 2-Way Set-Associative (LRU)": get_part3_exercise,
    "Simple Direct-Mapped": get_simple_direct_mapped_exercise,
    "Write Operations": get_write_exercise,
}


def get_exercise_names() -> list:
    return list(EXERCISE_REGISTRY.keys())


def load_exercise(name: str, memory) -> list:
    if name in EXERCISE_REGISTRY:
        return EXERCISE_REGISTRY[name](memory)
    raise ValueError(f"Unknown exercise: {name}")
