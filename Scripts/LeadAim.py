import pygame
import math
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions and settings
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turret Leading Shots")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)  # Color for the lead indicator and line
CYAN = (0, 255, 255)

# Turret and projectile settings
TURRET_RADIUS = 25
PROJECTILE_RADIUS = 15
PROJECTILE_SPEED = 15
RELOAD_TIME = 0.5  # Time in seconds between shots

# Initialize target settings
target_radius = 15
target_x = WIDTH // 2
target_y = HEIGHT // 2
target_angle = random.uniform(0, 2 * math.pi)
target_speed = random.uniform(2, 5)
target_velocity = [
    target_speed * math.cos(target_angle),
    target_speed * math.sin(target_angle),
]

# Initialize turret settings
turret_x = 100
turret_y = HEIGHT // 2
last_shot_time = 0  # Track the time when the last shot was fired


# Function to draw target
def draw_target(x, y):
    pygame.draw.circle(screen, BLUE, (int(x), int(y)), target_radius)


# Function to draw turret
def draw_turret(x, y):
    pygame.draw.circle(screen, GREEN, (int(x), int(y)), TURRET_RADIUS)


# Function to draw projectile
def draw_projectile(x, y):
    pygame.draw.circle(screen, RED, (int(x), int(y)), PROJECTILE_RADIUS)


# Function to draw line to lead position
def draw_line_to_target(turret_pos, target_pos):
    pygame.draw.line(screen, BLACK, turret_pos, target_pos, 2)


# Function to draw line to lead position
def draw_line_to_lead(turret_pos, lead_pos):
    pygame.draw.line(screen, RED, turret_pos, lead_pos, 2)


# Function to check collision
def check_collision(px, py, tx, ty):
    distance = math.sqrt((px - tx) ** 2 + (py - ty) ** 2)
    return distance < target_radius + PROJECTILE_RADIUS


# Function to calculate lead time
def calculate_lead_time(target_pos, target_vel, projectile_speed):
    tx, ty = target_pos
    tvx, tvy = target_vel
    dx = tx - turret_x
    dy = ty - turret_y
    a = tvx**2 + tvy**2 - projectile_speed**2
    b = 2 * (dx * tvx + dy * tvy)
    c = dx**2 + dy**2
    discriminant = b**2 - 4 * a * c

    if discriminant >= 0:
        t1 = (-b - math.sqrt(discriminant)) / (2 * a)
        t2 = (-b + math.sqrt(discriminant)) / (2 * a)
        if t1 > 0 and (t1 < t2 or t2 < 0):
            return t1
        if t2 > 0:
            return t2
    return -1


# Function to calculate lead position
def calculate_lead_position(target_pos, target_vel, lead_time):
    tx, ty = target_pos
    tvx, tvy = target_vel
    lead_x = tx + tvx * lead_time
    lead_y = ty + tvy * lead_time
    return lead_x, lead_y



# Function to calculate projectile trajectory
def calculate_trajectory(turret_pos, lead_pos, target_pos, steps=50):
    trajectory_points = []
    x, y = turret_pos
    lx, ly = lead_pos
    tx, ty = target_pos

    for step in range(steps):
        t = step / steps
        # Quadratic Bézier curve
        nx = (1 - t) ** 2 * x + 2 * (1 - t) * t * lx + t**2 * tx
        ny = (1 - t) ** 2 * y + 2 * (1 - t) * t * ly + t**2 * ty
        trajectory_points.append((nx, ny))

    return trajectory_points


# Main loop
running = True
clock = pygame.time.Clock()
projectiles = []
lead_x, lead_y = None, None  # Initialize lead position

while running:
    screen.fill(WHITE)

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Move turret to clicked position
            turret_x, turret_y = event.pos

    # Update target position
    target_x += target_velocity[0]
    target_y += target_velocity[1]

    # Check boundaries and update velocity to stay within screen
    if target_x - target_radius < 0 or target_x + target_radius > WIDTH:
        target_velocity[0] = -target_velocity[0]
    if target_y - target_radius < 0 or target_y + target_radius > HEIGHT:
        target_velocity[1] = -target_velocity[1]

    # Calculate lead position and draw lead indicator
    lead_time = calculate_lead_time(
        (target_x, target_y), target_velocity, PROJECTILE_SPEED
    )
    if lead_time > 0:
        lead_x, lead_y = calculate_lead_position(
            (target_x, target_y), target_velocity, lead_time
        )
        draw_line_to_target((turret_x, turret_y), (target_x, target_y))
        draw_line_to_lead((turret_x, turret_y), (lead_x, lead_y))

        # Calculate and draw trajectory
        trajectory_points = calculate_trajectory(
            (turret_x, turret_y), (lead_x, lead_y), (target_x, target_y)
        )
        if len(trajectory_points) > 1:
            pygame.draw.lines(screen, CYAN, False, trajectory_points, 2)

    # Fire projectile if reload time has passed
    current_time = time.time()
    if (
        current_time - last_shot_time >= RELOAD_TIME
        and lead_x is not None
        and lead_y is not None
    ):
        projectile_dx = lead_x - turret_x
        projectile_dy = lead_y - turret_y
        length = math.sqrt(projectile_dx**2 + projectile_dy**2)
        if length != 0:
            projectile_dx /= length
            projectile_dy /= length
        projectiles.append(
            [
                turret_x,
                turret_y,
                projectile_dx * PROJECTILE_SPEED,
                projectile_dy * PROJECTILE_SPEED,
            ]
        )
        last_shot_time = current_time

    # Update projectiles
    for projectile in projectiles[:]:
        projectile[0] += projectile[2]
        projectile[1] += projectile[3]
        if check_collision(projectile[0], projectile[1], target_x, target_y):
            projectiles.remove(projectile)

            # Bounce the target on hit
            target_velocity[0] = -target_velocity[0]
            target_velocity[1] = -target_velocity[1]

            # Change speed and direction
            target_speed = random.uniform(2, 5)
            target_angle = random.uniform(0, 2 * math.pi)
            target_velocity = [
                target_speed * math.cos(target_angle),
                target_speed * math.sin(target_angle),
            ]

        elif (
            projectile[0] < 0
            or projectile[0] > WIDTH
            or projectile[1] < 0
            or projectile[1] > HEIGHT
        ):
            projectiles.remove(projectile)

    # Draw everything
    draw_target(target_x, target_y)
    draw_turret(turret_x, turret_y)
    for px, py, vx, vy in projectiles:
        draw_projectile(px, py)

    pygame.display.flip()
    clock.tick(61)

pygame.quit()
