def calculate_difficulty(room_id: int) -> int:
    """
    Calculate difficulty level based on room ID.

    Difficulty increases every 10 rooms, capped at 10:
    - Rooms 0-9: difficulty 0
    - Rooms 10-19: difficulty 1
    - Rooms 20-29: difficulty 2
    - ...
    - Rooms 100+: difficulty 10 (max)

    Args:
        room_id: The current room ID (0-indexed)

    Returns:
        Difficulty level (0-10)
    """
    return min(10, max(0, room_id // 10))
