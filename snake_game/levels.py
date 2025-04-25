#!/usr/bin/env python3

class Level:
    """Class to define level properties"""
    def __init__(self, number, name, snake_speed, wall_positions=None, description=None):
        self.number = number
        self.name = name
        self.snake_speed = snake_speed  # frames per second
        self.wall_positions = wall_positions or []
        self.description = description or f"Level {number}: {name}"
        
    def get_walls(self):
        return self.wall_positions

def create_levels():
    """Create and return a list of levels"""
    levels = []
    
    # Level 1: Beginner
    levels.append(Level(
        number=1,
        name="Beginner",
        snake_speed=10,
        wall_positions=[],
        description="Level 1: Beginner - No walls, slow speed. Perfect for learning the game."
    ))
    
    # Level 2: Easy
    level2_walls = []
    # Add some simple walls in the middle
    for i in range(10, 20):
        level2_walls.append((i, 10))
    
    levels.append(Level(
        number=2,
        name="Easy",
        snake_speed=12,
        wall_positions=level2_walls,
        description="Level 2: Easy - A single wall in the middle and slightly faster speed."
    ))
    
    # Level 3: Intermediate
    level3_walls = []
    # Add walls in an L shape
    for i in range(5, 15):
        level3_walls.append((i, 5))
    for i in range(6, 15):
        level3_walls.append((15, i))
    
    levels.append(Level(
        number=3,
        name="Intermediate",
        snake_speed=15,
        wall_positions=level3_walls,
        description="Level 3: Intermediate - L-shaped walls and increased speed."
    ))
    
    # Level 4: Advanced
    level4_walls = []
    # Add walls in a box shape with openings
    for i in range(5, 25):
        if i != 15:  # Leave an opening
            level4_walls.append((i, 5))
            level4_walls.append((i, 25))
    for i in range(6, 25):
        if i != 15:  # Leave an opening
            level4_walls.append((5, i))
            level4_walls.append((25, i))
    
    levels.append(Level(
        number=4,
        name="Advanced",
        snake_speed=18,
        wall_positions=level4_walls,
        description="Level 4: Advanced - Box-shaped walls with openings and fast speed."
    ))
    
    # Level 5: Expert
    level5_walls = []
    # Create a maze-like structure
    for i in range(5, 25):
        if i % 5 != 0:  # Leave openings every 5 units
            level5_walls.append((i, 10))
            level5_walls.append((i, 20))
    for i in range(5, 25):
        if i % 5 != 0:  # Leave openings every 5 units
            level5_walls.append((10, i))
            level5_walls.append((20, i))
    
    levels.append(Level(
        number=5,
        name="Expert",
        snake_speed=20,
        wall_positions=level5_walls,
        description="Level 5: Expert - Maze-like walls and very fast speed. Only for the brave!"
    ))
    
    return levels 