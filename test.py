import pygame
import random
import math

pygame.init()

BACKGROUND_GRAY = (150, 150, 160)
SKIN_COLOR = (222, 184, 135)
BROWN = (139, 69, 19)
GRASS_GREEN = (70, 150, 70)
BLACK = (0, 0, 0)
STONE_DARK_GRAY = (160, 160, 160)
SCRAP_BLACK = (20, 20, 20)
BUSH_GREEN = (40, 120, 40)
WHITE = (255, 255, 255)

screen_width = 1000
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))

survivor_health = 100
survivor_hunger = 0
survivor_stamina = 100
food = 10
materials = 5
components = 3
medicine = 0
bullets = 0
fortress_health = 100
current_day = 1

survivor_speed = 3
survivor_radius = 20 # Player is a circle, this is its radius

# --- Player Setup ---
# The survivor_rect is still useful for general positioning, but we'll use
# survivor_radius for accurate circular collision
survivor_rect = pygame.Rect(
    0,
    0,
    survivor_radius * 2,
    survivor_radius * 2
)

player_screen_draw_rect = pygame.Rect(
    screen_width / 2 - survivor_radius,
    screen_height / 2 - survivor_radius,
    survivor_radius * 2,
    survivor_radius * 2
)

# --- House Setup (All in WORLD Coordinates) ---
wall_thickness = 20

house_center_world_x = 0
house_center_world_y = 0

top_wall_length = screen_width / 5
bottom_wall_length = top_wall_length

house_top_left_world_x = int(house_center_world_x - top_wall_length / 2)
house_top_left_world_y = int(house_center_world_y - top_wall_length / 2)
top_wall_length = int(top_wall_length)

top_wall_rect = pygame.Rect(
    house_top_left_world_x,
    house_top_left_world_y,
    top_wall_length,
    wall_thickness
)
bottom_wall_rect = pygame.Rect(
    house_top_left_world_x,
    house_top_left_world_y + top_wall_length - wall_thickness,
    top_wall_length,
    wall_thickness
)

left_wall_rect = pygame.Rect(
    house_top_left_world_x,
    house_top_left_world_y + wall_thickness,
    wall_thickness,
    top_wall_length - (2 * wall_thickness)
)

right_wall_x_pos = house_top_left_world_x + top_wall_length - wall_thickness
inner_house_height = top_wall_length - (2 * wall_thickness)

right_wall_top_height = inner_house_height // 3
right_wall_bottom_height = inner_house_height // 3
door_gap_height = inner_house_height - (right_wall_top_height + right_wall_bottom_height)

if right_wall_top_height < 0: right_wall_top_height = 0
if right_wall_bottom_height < 0: right_wall_bottom_height = 0
if door_gap_height < 0: door_gap_height = 0

right_wall_top_rect = pygame.Rect(
    right_wall_x_pos,
    house_top_left_world_y + wall_thickness,
    wall_thickness,
    right_wall_top_height
)

right_wall_bottom_rect = pygame.Rect(
    right_wall_x_pos,
    right_wall_top_rect.bottom + door_gap_height,
    wall_thickness,
    right_wall_bottom_height
)

ALL_WALL_RECTS = [
    top_wall_rect,
    bottom_wall_rect,
    left_wall_rect,
    right_wall_top_rect,
    right_wall_bottom_rect
]

survivor_rect.centerx = right_wall_top_rect.right + survivor_radius + 5
survivor_rect.centery = right_wall_top_rect.bottom + (door_gap_height // 2)

# --- World Objects (Stones, Scraps, Bushes) ---
WORLD_BOUNDS_X_MIN = -1000
WORLD_BOUNDS_X_MAX = 1000
WORLD_BOUNDS_Y_MIN = -1000
WORLD_BOUNDS_Y_MAX = 1000

def generate_random_objects(min_count, max_count, min_size, max_size):
    objects = []
    num_objects = random.randint(min_count, max_count)
    for _ in range(num_objects):
        size = random.randint(min_size, max_size)
        x = random.randint(WORLD_BOUNDS_X_MIN, WORLD_BOUNDS_X_MAX - size)
        y = random.randint(WORLD_BOUNDS_Y_MIN, WORLD_BOUNDS_Y_MAX - size)
        objects.append(pygame.Rect(x, y, size, size)) # Still store as Rect for drawing and initial bounds
    return objects

ALL_STONES = generate_random_objects(5, 15, 25, 60)
ALL_SCRAPS = generate_random_objects(3, 10, 30, 50)
ALL_BUSHES = generate_random_objects(5, 12, 40, 70)

# We now separate rectangular and circular collidable objects
RECT_COLLIDABLE_OBJECTS = ALL_WALL_RECTS + ALL_SCRAPS # Scraps are still rectangles
CIRCLE_COLLIDABLE_OBJECTS = ALL_STONES + ALL_BUSHES # Stones and Bushes are now circles for collision

# --- Helper function for circular collision detection ---
def check_circle_collision_and_resolve(player_center, player_radius, object_rect_world, object_radius, move_x, move_y):
    object_center_x = object_rect_world.centerx
    object_center_y = object_rect_world.centery

    # Calculate the distance between centers
    dx = player_center[0] - object_center_x
    dy = player_center[1] - object_center_y
    distance = math.sqrt(dx**2 + dy**2)

    # Sum of radii for collision
    min_distance = player_radius + object_radius

    if distance < min_distance:
        # Collision detected!
        if distance == 0: # Avoid division by zero if centers are exactly the same
            distance = 0.01

        # Calculate overlap
        overlap = min_distance - distance

        # Calculate unit vector of collision normal
        normal_x = dx / distance
        normal_y = dy / distance

        # Push the player out along the collision normal
        # We only apply this push if the player was moving towards the object
        # This prevents "sticking" if the player is already deeply overlapping
        dot_product = move_x * normal_x + move_y * normal_y
        if dot_product < 0: # Player was moving into the object
            push_back_x = normal_x * overlap
            push_back_y = normal_y * overlap
            return (push_back_x, push_back_y)
    return (0, 0) # No collision or no push back needed

# --- Game Loop ---
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Player Input ---
    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    if keys[pygame.K_LEFT]:
        dx = -1
    if keys[pygame.K_RIGHT]:
        dx = 1
    if keys[pygame.K_UP]:
        dy = -1
    if keys[pygame.K_DOWN]:
        dy = 1

    magnitude = math.sqrt(dx**2 + dy**2)
    if magnitude > 0:
        move_x_world = dx / magnitude * survivor_speed
        move_y_world = dy / magnitude * survivor_speed
    else:
        move_x_world = 0
        move_y_world = 0

    # Store the original position before attempting to move
    original_survivor_x = survivor_rect.x
    original_survivor_y = survivor_rect.y

    # --- PLAYER MOVEMENT AND COLLISION RESOLUTION ---

    # 1. Handle Rectangular Collisions (Walls, Scraps)
    # Attempt to move in X
    survivor_rect.x += move_x_world
    for obj_rect in RECT_COLLIDABLE_OBJECTS:
        if survivor_rect.colliderect(obj_rect):
            if move_x_world > 0:
                survivor_rect.right = obj_rect.left
            elif move_x_world < 0:
                survivor_rect.left = obj_rect.right
            # No break here in case multiple rects are overlapping
            # (though with walls this is less likely, but good for other rects)

    # Attempt to move in Y
    survivor_rect.y += move_y_world
    for obj_rect in RECT_COLLIDABLE_OBJECTS:
        if survivor_rect.colliderect(obj_rect):
            if move_y_world > 0:
                survivor_rect.bottom = obj_rect.top
            elif move_y_world < 0:
                survivor_rect.top = obj_rect.bottom
            # No break here

    # 2. Handle Circular Collisions (Stones, Bushes)
    # Get current player center after rectangular collisions
    player_current_center = survivor_rect.center
    
    # Accumulate push-backs from all circular objects
    total_push_back_x = 0
    total_push_back_y = 0

    for obj_rect_world in CIRCLE_COLLIDABLE_OBJECTS:
        # For circular objects, the radius is half their width/height
        obj_radius = obj_rect_world.width // 2
        
        # Calculate push-back
        push_x, push_y = check_circle_collision_and_resolve(
            player_current_center, survivor_radius,
            obj_rect_world, obj_radius,
            move_x_world, move_y_world # Pass the attempted movement to help resolve
        )
        total_push_back_x += push_x
        total_push_back_y += push_y
    
    # Apply the accumulated push-back from circular collisions
    survivor_rect.x += total_push_back_x
    survivor_rect.y += total_push_back_y


    # --- Update Camera Offset ---
    camera_offset_x = survivor_rect.centerx - screen_width / 2
    camera_offset_y = survivor_rect.centery - screen_height / 2

    # --- Drawing ---
    screen.fill(GRASS_GREEN)

    screen_rect_for_check = screen.get_rect()

    # Draw the house walls
    for wall_rect_world in ALL_WALL_RECTS:
        wall_screen_rect = wall_rect_world.move(-camera_offset_x, -camera_offset_y)
        if wall_screen_rect.colliderect(screen_rect_for_check):
            pygame.draw.rect(screen, BROWN, wall_screen_rect)

    # Draw Stones (now perfect circles)
    for stone_rect_world in ALL_STONES:
        stone_screen_rect = stone_rect_world.move(-camera_offset_x, -camera_offset_y)
        if stone_screen_rect.colliderect(screen_rect_for_check):
            # 1. Draw black outline
            outline_thickness = 3
            outline_rect = stone_screen_rect.inflate(outline_thickness * 2, outline_thickness * 2)
            pygame.draw.ellipse(screen, BLACK, outline_rect)

            # 2. Draw the main stone body
            pygame.draw.ellipse(screen, STONE_DARK_GRAY, stone_screen_rect)

            # 3. Draw a small white highlight circle
            highlight_radius = max(2, int(stone_screen_rect.width * 0.15))
            highlight_offset_x = -int(stone_screen_rect.width * 0.1)
            highlight_offset_y = -int(stone_screen_rect.height * 0.1)
            pygame.draw.circle(
                screen,
                WHITE,
                (stone_screen_rect.centerx + highlight_offset_x, stone_screen_rect.centery + highlight_offset_y),
                highlight_radius
            )

    # Draw Scraps (Black Boxes)
    for scrap_rect_world in ALL_SCRAPS:
        scrap_screen_rect = scrap_rect_world.move(-camera_offset_x, -camera_offset_y)
        if scrap_screen_rect.colliderect(screen_rect_for_check):
            pygame.draw.rect(screen, SCRAP_BLACK, scrap_screen_rect)

    # Draw Bushes
    for bush_rect_world in ALL_BUSHES:
        bush_screen_rect = bush_rect_world.move(-camera_offset_x, -camera_offset_y)
        if bush_screen_rect.colliderect(screen_rect_for_check):
            pygame.draw.circle(screen, BUSH_GREEN, bush_screen_rect.center, bush_screen_rect.width // 2)


    # Draw the player body
    pygame.draw.ellipse(screen, SKIN_COLOR, player_screen_draw_rect)

    pygame.display.flip()
    pygame.time.Clock().tick(60)

pygame.quit()
