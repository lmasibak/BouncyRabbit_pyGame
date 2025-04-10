import pygame
import sys
import random
import math
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncy Rabbit")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)

# Game variables
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 24)
large_font = pygame.font.SysFont('Arial', 40)
title_font = pygame.font.SysFont('Arial', 60, bold=True)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
LEVEL_COMPLETE = 3
game_state = MENU

# Sound effects (using simple beeps since we can't load external files)
def play_jump_sound():
    jump_sound = mixer.Sound(pygame.sndarray.array(pygame.Surface((1, 1))))
    jump_sound.set_volume(0.2)
    jump_sound.play()

def play_death_sound():
    death_sound = mixer.Sound(pygame.sndarray.array(pygame.Surface((1, 1))))
    death_sound.set_volume(0.3)
    death_sound.play()

def play_level_up_sound():
    level_up_sound = mixer.Sound(pygame.sndarray.array(pygame.Surface((1, 1))))
    level_up_sound.set_volume(0.4)
    level_up_sound.play()

# Rabbit class
class Rabbit:
    def __init__(self):
        self.radius = 20
        self.x = 100
        self.y = HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.6
        self.jump_strength = -12
        self.is_jumping = False
        self.rotation = 0
        self.ear_length = 15
        
    def jump(self):
        if not self.is_jumping:
            self.velocity = self.jump_strength
            self.is_jumping = True
            play_jump_sound()
    
    def update(self):
        # Apply gravity
        self.velocity += self.gravity
        self.y += self.velocity
        
        # Rotate based on velocity
        self.rotation = min(max(self.velocity * 3, -45), 45)
        
        # Check floor and ceiling
        if self.y >= HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.velocity = 0
            self.is_jumping = False
        
        if self.y <= self.radius:
            self.y = self.radius
            self.velocity = 0
    
    def draw(self):
        # Draw rabbit body (circle)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        
        # Draw rabbit face details
        eye_x = self.x + 5
        eye_y = self.y - 5
        pygame.draw.circle(screen, BLACK, (int(eye_x), int(eye_y)), 4)
        
        # Draw ears (rotated based on velocity)
        angle_rad = math.radians(self.rotation)
        ear1_x = self.x - 5
        ear1_y = self.y - 15
        ear2_x = self.x + 5
        ear2_y = self.y - 15
        
        # Calculate ear positions with rotation
        ear1_end_x = ear1_x - self.ear_length * math.sin(angle_rad)
        ear1_end_y = ear1_y - self.ear_length * math.cos(angle_rad)
        ear2_end_x = ear2_x - self.ear_length * math.sin(angle_rad)
        ear2_end_y = ear2_y - self.ear_length * math.cos(angle_rad)
        
        pygame.draw.line(screen, WHITE, (ear1_x, ear1_y), (ear1_end_x, ear1_end_y), 3)
        pygame.draw.line(screen, WHITE, (ear2_x, ear2_y), (ear2_end_x, ear2_end_y), 3)
    
    def check_collision(self, obstacles):
        for obstacle in obstacles:
            if obstacle.collide(self.x, self.y, self.radius):
                return True
        return False

# Obstacle class
class Obstacle:
    def __init__(self, x, y, width, height, speed, obstacle_type="rectangle"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.type = obstacle_type
        self.passed = False
        self.oscillation_speed = random.uniform(0.02, 0.05)
        self.oscillation_amplitude = random.randint(20, 80)
        self.start_y = y
        self.angle = random.uniform(0, 2 * math.pi)
    
    def update(self, level_speed):
        self.x -= self.speed * level_speed
        
        # Different movement patterns based on obstacle type
        if self.type == "oscillating":
            self.angle += self.oscillation_speed
            self.y = self.start_y + math.sin(self.angle) * self.oscillation_amplitude
        elif self.type == "zigzag":
            self.angle += self.oscillation_speed * 2
            self.y = self.start_y + math.sin(self.angle) * self.oscillation_amplitude
    
    def draw(self):
        if self.type == "rectangle":
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
        elif self.type == "spikes":
            # Draw a series of triangles
            spike_width = self.width / 5
            for i in range(5):
                spike_x = self.x + i * spike_width
                pygame.draw.polygon(screen, WHITE, [
                    (spike_x, self.y + self.height),
                    (spike_x + spike_width/2, self.y),
                    (spike_x + spike_width, self.y + self.height)
                ])
        elif self.type in ["oscillating", "zigzag"]:
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
    
    def collide(self, rabbit_x, rabbit_y, rabbit_radius):
        # Simplified circle-rectangle collision
        closest_x = max(self.x, min(rabbit_x, self.x + self.width))
        closest_y = max(self.y, min(rabbit_y, self.y + self.height))
        
        distance_x = rabbit_x - closest_x
        distance_y = rabbit_y - closest_y
        
        return (distance_x ** 2 + distance_y ** 2) < (rabbit_radius ** 2)

# Game manager
class GameManager:
    def __init__(self):
        self.reset_game()
    
    def reset_game(self):
        self.level = 1
        self.score = 0
        self.obstacles = []
        self.rabbit = Rabbit()
        self.obstacle_timer = 0
        self.obstacle_frequency = 120  # Frames between obstacles
        self.level_speed = 1.0
        self.level_progress = 0
        self.level_length = 20  # Number of obstacles to clear a level
        
    def update(self):
        # Update rabbit
        self.rabbit.update()
        
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle.update(self.level_speed)
            
            # Remove obstacles that are off-screen
            if obstacle.x + obstacle.width < 0:
                self.obstacles.remove(obstacle)
                self.score += 10
                self.level_progress += 1
                
                # Check if level is complete
                if self.level_progress >= self.level_length:
                    self.level_up()
        
        # Check collisions
        if self.rabbit.check_collision(self.obstacles):
            play_death_sound()
            global game_state
            game_state = GAME_OVER
        
        # Spawn new obstacles
        self.obstacle_timer += 1
        if self.obstacle_timer >= self.obstacle_frequency:
            self.spawn_obstacle()
            self.obstacle_timer = 0
    
    def level_up(self):
        global game_state
        if self.level < 45:
            self.level += 1
            self.level_progress = 0
            self.level_speed = 1.0 + (self.level * 0.1)  # Increase speed with level
            self.obstacle_frequency = max(40, 120 - (self.level * 2))  # Decrease time between obstacles
            play_level_up_sound()
            game_state = LEVEL_COMPLETE
        else:
            # Game completed
            game_state = GAME_OVER
    
    def spawn_obstacle(self):
        # Different obstacle types based on level
        obstacle_types = ["rectangle"]
        if self.level >= 5:
            obstacle_types.append("spikes")
        if self.level >= 10:
            obstacle_types.append("oscillating")
        if self.level >= 20:
            obstacle_types.append("zigzag")
        
        obstacle_type = random.choice(obstacle_types)
        
        # Randomize obstacle dimensions based on level
        height = random.randint(50, 150 + min(self.level * 3, 150))
        width = random.randint(30, 50 + min(self.level, 30))
        
        # Randomize position
        if random.random() < 0.5:
            # Obstacle on the ground
            y = HEIGHT - height
        else:
            # Obstacle on the ceiling
            y = 0
        
        # Create obstacle
        speed = 5 + (self.level * 0.2)
        obstacle = Obstacle(WIDTH, y, width, height, speed, obstacle_type)
        self.obstacles.append(obstacle)
    
    def draw(self):
        # Draw background
        screen.fill(BLACK)
        
        # Draw ground line
        pygame.draw.line(screen, GRAY, (0, HEIGHT - 1), (WIDTH, HEIGHT - 1), 2)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw()
        
        # Draw rabbit
        self.rabbit.draw()
        
        # Draw HUD
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        level_text = font.render(f"Level: {self.level}/45", True, WHITE)
        progress_text = font.render(f"Progress: {self.level_progress}/{self.level_length}", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 40))
        screen.blit(progress_text, (10, 70))

# Create game manager
game_manager = GameManager()

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == MENU:
                game_state = PLAYING
            elif game_state == PLAYING:
                game_manager.rabbit.jump()
            elif game_state == GAME_OVER:
                game_manager.reset_game()
                game_state = MENU
            elif game_state == LEVEL_COMPLETE:
                game_state = PLAYING
    
    # Handle different game states
    if game_state == MENU:
        screen.fill(BLACK)
        title = title_font.render("BOUNCY RABBIT", True, WHITE)
        subtitle = large_font.render("Click to Start", True, LIGHT_GRAY)
        
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2 + 50))
        
        # Draw a simple rabbit icon
        pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2 - 20), 30)
        pygame.draw.circle(screen, BLACK, (WIDTH//2 + 10, HEIGHT//2 - 30), 5)
        pygame.draw.line(screen, WHITE, (WIDTH//2 - 10, HEIGHT//2 - 40), (WIDTH//2 - 20, HEIGHT//2 - 70), 4)
        pygame.draw.line(screen, WHITE, (WIDTH//2 + 10, HEIGHT//2 - 40), (WIDTH//2 + 20, HEIGHT//2 - 70), 4)
        
    elif game_state == PLAYING:
        game_manager.update()
        game_manager.draw()
        
    elif game_state == GAME_OVER:
        screen.fill(BLACK)
        
        if game_manager.level >= 45:
            title = large_font.render("CONGRATULATIONS!", True, WHITE)
            subtitle = font.render(f"You completed all 45 levels with a score of {game_manager.score}!", True, LIGHT_GRAY)
        else:
            title = large_font.render("GAME OVER", True, WHITE)
            subtitle = font.render(f"Final Score: {game_manager.score} - Level: {game_manager.level}", True, LIGHT_GRAY)
        
        instruction = font.render("Click to return to menu", True, GRAY)
        
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2))
        screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 100))
        
    elif game_state == LEVEL_COMPLETE:
        screen.fill(BLACK)
        
        title = large_font.render(f"LEVEL {game_manager.level-1} COMPLETE!", True, WHITE)
        subtitle = font.render(f"Score: {game_manager.score}", True, LIGHT_GRAY)
        next_level = font.render(f"Get ready for Level {game_manager.level}...", True, LIGHT_GRAY)
        instruction = font.render("Click to continue", True, GRAY)
        
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2))
        screen.blit(next_level, (WIDTH//2 - next_level.get_width()//2, HEIGHT//2 + 50))
        screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 100))
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()