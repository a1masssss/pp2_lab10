s#!/usr/bin/env python3

import pygame
import sys
import random
import time
from db_utils import SnakeGameDB
from levels import create_levels

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# Directions
UP = 'UP'
DOWN = 'DOWN'
LEFT = 'LEFT'
RIGHT = 'RIGHT'

class Snake:
    def __init__(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.length = 1
        self.direction = RIGHT
        self.color = GREEN
        self.score = 0
        
    def get_head_position(self):
        return self.positions[0]
        
    def update(self):
        head = self.get_head_position()
        x, y = head
        
        if self.direction == UP:
            y -= 1
        elif self.direction == DOWN:
            y += 1
        elif self.direction == LEFT:
            x -= 1
        elif self.direction == RIGHT:
            x += 1
            
        # Wrap around screen edges
        if x < 0:
            x = GRID_WIDTH - 1
        elif x >= GRID_WIDTH:
            x = 0
        if y < 0:
            y = GRID_HEIGHT - 1
        elif y >= GRID_HEIGHT:
            y = 0
            
        new_head = (x, y)
        self.positions.insert(0, new_head)
        
        if len(self.positions) > self.length:
            self.positions.pop()
            
    def render(self, surface):
        for position in self.positions:
            rect = pygame.Rect(
                position[0] * GRID_SIZE,
                position[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, WHITE, rect, 1)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()
        
    def randomize_position(self, occupied_positions=None):
        occupied_positions = occupied_positions if occupied_positions else []
        while True:
            self.position = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            if self.position not in occupied_positions:
                break
    
    def render(self, surface):
        rect = pygame.Rect(
            self.position[0] * GRID_SIZE,
            self.position[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, WHITE, rect, 1)

class Game:
    def __init__(self, username):
        # Set up the game window
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Snake Game - {username}")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.font_large = pygame.font.SysFont('Arial', 36)
        
        # Init game objects
        self.snake = Snake()
        self.food = Food()
        
        # Load game levels
        self.levels = create_levels()
        
        # Database connection
        self.db = SnakeGameDB()
        if not self.db.connect():
            print("Failed to connect to database. Exiting.")
            pygame.quit()
            sys.exit()
            
        # User data
        self.username = username
        self.user_id = self.db.get_or_create_user(username)
        self.level = self.db.get_user_highest_level(self.user_id)
        self.highest_score = self.db.get_user_highest_score(self.user_id)
        
        # Initialize level
        self.current_level = self.levels[min(self.level, len(self.levels)) - 1]
        
        # Game state
        self.running = True
        self.paused = False
        
        # Try to load the last game state
        self.load_game_state()
        
    def load_game_state(self):
        """Try to load the last saved game state"""
        game_state = self.db.load_last_game_state(self.user_id)
        if game_state:
            # Set level
            self.level = game_state['level']
            self.current_level = self.levels[min(self.level, len(self.levels)) - 1]
            
            # Set snake position and score
            self.snake.positions = game_state['snake_positions']
            self.snake.length = len(self.snake.positions)
            self.snake.score = game_state['score']
            self.snake.direction = game_state['direction']
            
            # Set food position
            self.food.position = game_state['food_pos']
            
            print(f"Game state loaded for {self.username}!")
            
    def save_game_state(self):
        """Save the current game state to the database"""
        if self.user_id:
            self.db.save_game_state(
                self.user_id,
                self.level,
                self.snake.score,
                self.snake.positions,
                self.food.position,
                self.snake.direction
            )
            print("Game state saved!")
            
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # Handle key presses
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                    
                # Pause game and save state with 'p' key
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    if self.paused:
                        self.save_game_state()
                        
                # Direction controls (prevent 180-degree turns)
                if not self.paused:
                    if event.key == pygame.K_UP and self.snake.direction != DOWN:
                        self.snake.direction = UP
                    elif event.key == pygame.K_DOWN and self.snake.direction != UP:
                        self.snake.direction = DOWN
                    elif event.key == pygame.K_LEFT and self.snake.direction != RIGHT:
                        self.snake.direction = LEFT
                    elif event.key == pygame.K_RIGHT and self.snake.direction != LEFT:
                        self.snake.direction = RIGHT
                        
    def check_collisions(self):
        """Check for collisions with food, walls, or self"""
        head = self.snake.get_head_position()
        
        # Check for food collision
        if head == self.food.position:
            self.snake.length += 1
            self.snake.score += 10
            # Update highest score if needed
            if self.snake.score > self.highest_score:
                self.highest_score = self.snake.score
            
            # If score reaches a threshold, unlock next level
            if self.snake.score >= self.level * 50 and self.level < len(self.levels):
                self.level += 1
                self.current_level = self.levels[self.level - 1]
                
            # Generate new food
            occupied_positions = self.snake.positions + self.current_level.get_walls()
            self.food.randomize_position(occupied_positions)
        
        # Check for self collision (except the head)
        if head in self.snake.positions[1:]:
            self.game_over()
            return True
            
        # Check for wall collision
        if head in self.current_level.get_walls():
            self.game_over()
            return True
            
        return False
        
    def game_over(self):
        """Handle game over state"""
        self.screen.fill(BLACK)
        
        # Display game over message
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.snake.score}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        restart_text = self.font.render("Press ENTER to restart or ESC to quit", True, WHITE)
        
        self.screen.blit(game_over_text, 
                        (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 
                        WINDOW_HEIGHT // 2 - 60))
        self.screen.blit(score_text, 
                        (WINDOW_WIDTH // 2 - score_text.get_width() // 2, 
                        WINDOW_HEIGHT // 2))
        self.screen.blit(level_text, 
                        (WINDOW_WIDTH // 2 - level_text.get_width() // 2, 
                        WINDOW_HEIGHT // 2 + 30))
        self.screen.blit(restart_text, 
                        (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 
                        WINDOW_HEIGHT // 2 + 80))
        
        pygame.display.update()
        
        waiting_for_key = True
        while waiting_for_key:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting_for_key = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Reset the game
                        self.snake = Snake()
                        occupied_positions = self.snake.positions + self.current_level.get_walls()
                        self.food.randomize_position(occupied_positions)
                        waiting_for_key = False
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        waiting_for_key = False
    
    def render_walls(self):
        """Render the walls for the current level"""
        for wall_pos in self.current_level.get_walls():
            rect = pygame.Rect(
                wall_pos[0] * GRID_SIZE,
                wall_pos[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(self.screen, GRAY, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 1)
    
    def render_ui(self):
        """Render UI elements"""
        # Display score
        score_text = self.font.render(f"Score: {self.snake.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Display level information
        level_text = self.font.render(f"Level {self.level}: {self.current_level.name}", True, WHITE)
        self.screen.blit(level_text, (WINDOW_WIDTH - level_text.get_width() - 10, 10))
        
        # Display high score
        high_score_text = self.font.render(f"High Score: {self.highest_score}", True, WHITE)
        self.screen.blit(high_score_text, (10, WINDOW_HEIGHT - 30))
        
        # Display pause instructions
        pause_text = self.font.render("Press 'P' to pause/save", True, WHITE)
        self.screen.blit(pause_text, (WINDOW_WIDTH - pause_text.get_width() - 10, WINDOW_HEIGHT - 30))
        
        # Display pause screen if paused
        if self.paused:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Black with alpha
            self.screen.blit(overlay, (0, 0))
            
            paused_text = self.font_large.render("PAUSED", True, WHITE)
            resume_text = self.font.render("Press 'P' to resume", True, WHITE)
            saved_text = self.font.render("Game state saved", True, GREEN)
            
            self.screen.blit(paused_text, 
                            (WINDOW_WIDTH // 2 - paused_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 - 40))
            self.screen.blit(resume_text, 
                            (WINDOW_WIDTH // 2 - resume_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 + 10))
            self.screen.blit(saved_text, 
                            (WINDOW_WIDTH // 2 - saved_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 + 40))
        
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            
            if not self.paused:
                # Update game state
                self.snake.update()
                
                # Check for collisions
                if self.check_collisions():
                    continue  # Restart the loop after game over
            
            # Render everything
            self.screen.fill(BLACK)
            self.snake.render(self.screen)
            self.food.render(self.screen)
            self.render_walls()
            self.render_ui()
            
            # Update the display
            pygame.display.update()
            
            # Control game speed based on level
            self.clock.tick(self.current_level.snake_speed)
        
        # Cleanup
        self.save_game_state()
        self.db.disconnect()
        pygame.quit()
        

def get_username():
    """Prompt for and return username"""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Snake Game - Login")
    font = pygame.font.SysFont('Arial', 24)
    input_font = pygame.font.SysFont('Arial', 32)
    
    username = ""
    input_active = True
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username:
                    return username
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key != pygame.K_RETURN:
                    username += event.unicode
        
        screen.fill(BLACK)
        
        # Display prompt
        title_text = font.render("Snake Game", True, GREEN)
        prompt_text = font.render("Enter your username:", True, WHITE)
        
        # Display input box
        input_box = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2, WINDOW_WIDTH // 2, 50)
        pygame.draw.rect(screen, WHITE, input_box, 2)
        
        # Display entered username
        username_surface = input_font.render(username, True, WHITE)
        screen.blit(username_surface, (input_box.x + 10, input_box.y + 10))
        
        # Display instruction
        instruction_text = font.render("Press ENTER to start", True, WHITE)
        
        # Blit texts to screen
        screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 100))
        screen.blit(prompt_text, (WINDOW_WIDTH // 2 - prompt_text.get_width() // 2, WINDOW_HEIGHT // 2 - 60))
        screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2 + 80))
        
        pygame.display.update()

if __name__ == "__main__":
    username = get_username()
    game = Game(username)
    game.run() 