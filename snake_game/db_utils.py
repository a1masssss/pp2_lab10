#!/usr/bin/env python3

import psycopg2
import sys
import json
sys.path.append("..")
from config import DB_CONFIG

class SnakeGameDB:
    def __init__(self):
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Connect to the PostgreSQL database server"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to the database: {error}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()

    def get_or_create_user(self, username):
        """Get user ID by username or create a new user if not exists"""
        # First try to get existing user
        sql = "SELECT id FROM users WHERE username = %s"
        try:
            self.cur.execute(sql, (username,))
            user = self.cur.fetchone()
            
            if user:
                return user[0]
            
            # If user doesn't exist, create a new user
            sql = "INSERT INTO users (username) VALUES (%s) RETURNING id"
            self.cur.execute(sql, (username,))
            user_id = self.cur.fetchone()[0]
            self.conn.commit()
            return user_id
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error with user operation: {error}")
            return None

    def get_user_highest_level(self, user_id):
        """Get the highest level achieved by the user"""
        sql = """
        SELECT MAX(level) FROM user_score 
        WHERE user_id = %s
        """
        try:
            self.cur.execute(sql, (user_id,))
            result = self.cur.fetchone()
            return result[0] if result and result[0] else 1
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting user level: {error}")
            return 1  # Default to level 1 on error

    def get_user_highest_score(self, user_id):
        """Get the highest score achieved by the user"""
        sql = """
        SELECT MAX(score) FROM user_score 
        WHERE user_id = %s
        """
        try:
            self.cur.execute(sql, (user_id,))
            result = self.cur.fetchone()
            return result[0] if result and result[0] else 0
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting user score: {error}")
            return 0
            
    def save_game_state(self, user_id, level, score, snake_positions, food_pos, direction):
        """Save the current game state to the database"""
        # Convert snake positions list to JSON string
        snake_x_json = json.dumps([pos[0] for pos in snake_positions])
        snake_y_json = json.dumps([pos[1] for pos in snake_positions])
        
        sql = """
        INSERT INTO user_score (user_id, level, score, snake_x_positions, snake_y_positions, food_x, food_y, direction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            self.cur.execute(sql, (
                user_id, 
                level, 
                score, 
                snake_x_json, 
                snake_y_json, 
                food_pos[0], 
                food_pos[1], 
                direction
            ))
            score_id = self.cur.fetchone()[0]
            self.conn.commit()
            return score_id
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error saving game state: {error}")
            return None
            
    def load_last_game_state(self, user_id):
        """Load the most recent game state for the user"""
        sql = """
        SELECT level, score, snake_x_positions, snake_y_positions, food_x, food_y, direction
        FROM user_score
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        try:
            self.cur.execute(sql, (user_id,))
            result = self.cur.fetchone()
            
            if not result:
                return None
                
            level, score, snake_x_json, snake_y_json, food_x, food_y, direction = result
            
            # Parse the JSON strings back to lists
            snake_x_positions = json.loads(snake_x_json)
            snake_y_positions = json.loads(snake_y_json)
            
            # Combine x and y coordinates into position tuples
            snake_positions = list(zip(snake_x_positions, snake_y_positions))
            
            return {
                'level': level,
                'score': score,
                'snake_positions': snake_positions,
                'food_pos': (food_x, food_y),
                'direction': direction
            }
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error loading game state: {error}")
            return None 