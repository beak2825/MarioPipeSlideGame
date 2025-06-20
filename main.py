import pygame
import sys
import os

# --- Init ---
pygame.init()

# --- Constants ---
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 600
FPS = 60

LINE_COUNT = 4
LINE_SPACING = WINDOW_WIDTH // (LINE_COUNT + 1)

MARIO_SIZE = 20
MARIO_SPEED = 2

PIPE_Y = WINDOW_HEIGHT - 40
MUSIC_FOLDER = "music/"
SOUNDS_FOLDER = "sounds/"
MAIN_MUSIC = MUSIC_FOLDER + "slides.mp3"
SOUND_PATH = SOUNDS_FOLDER + "scream.mp3"
DRAW_SOUND_PATH = SOUNDS_FOLDER + "line_drawing.mp3"
SNAP_SOUND_PATH = SOUNDS_FOLDER + "line_snap.mp3"

# --- Assets ---
if os.path.exists(MAIN_MUSIC):
    pygame.mixer.music.load(MAIN_MUSIC)
    pygame.mixer.music.play(-1)

scream_sound = pygame.mixer.Sound(SOUND_PATH) if os.path.exists(SOUND_PATH) else None
draw_sound = pygame.mixer.Sound(DRAW_SOUND_PATH) if os.path.exists(DRAW_SOUND_PATH) else None
snap_sound = pygame.mixer.Sound(SNAP_SOUND_PATH) if os.path.exists(SNAP_SOUND_PATH) else None

# --- Setup ---
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mario's Slides")
clock = pygame.time.Clock()

# --- Game Objects ---
lines_x = [LINE_SPACING * (i + 1) for i in range(LINE_COUNT)]
mario_x = lines_x[0] - MARIO_SIZE // 2
mario_y = 0

pipes = []
for i, x in enumerate(lines_x):
    rect = pygame.Rect(x - 10, PIPE_Y, 20, 20)
    color = (255, 255, 0) if i == LINE_COUNT - 1 else (0, 255, 0)  # star on the last pipe
    pipes.append((rect, color))

# --- Path Drawing ---
drawing = False
start_point = None
paths = []

# --- Main Loop ---
running = True
game_over = False
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = pygame.mouse.get_pos()
            # Snap to nearest line x
            nearest_x = min(lines_x, key=lambda x: abs(mx - x))
            if abs(mx - nearest_x) < 15:
                start_point = (nearest_x, my)
                drawing = True
                if draw_sound:
                    draw_sound.play(-1)

        if event.type == pygame.MOUSEBUTTONUP and drawing:
            mx, my = pygame.mouse.get_pos()
            nearest_x = min(lines_x, key=lambda x: abs(mx - x))
            if abs(mx - nearest_x) < 15:
                end_point = (nearest_x, my)
                if start_point[0] != end_point[0]:  # Ensure diagonal/side connection
                    paths.append((start_point, end_point))
                    if snap_sound:
                        snap_sound.play()
            drawing = False
            start_point = None
            if draw_sound:
                draw_sound.stop()

    if not game_over:
        mario_y += MARIO_SPEED

        # Check collision with pipes
        for rect, color in pipes:
            if rect.collidepoint(mario_x + MARIO_SIZE // 2, mario_y + MARIO_SIZE):
                if color != (255, 255, 0):  # not star
                    if scream_sound:
                        scream_sound.play()
                    game_over = True

    # --- Draw ---
    screen.fill((0, 0, 0))

    # Lines
    for x in lines_x:
        pygame.draw.line(screen, (255, 255, 255), (x, 0), (x, WINDOW_HEIGHT), 2)

    # Draw paths
    for start, end in paths:
        pygame.draw.line(screen, (0, 255, 255), start, end, 3)

    # Preview drawing
    if drawing and start_point:
        mx, my = pygame.mouse.get_pos()
        nearest_x = min(lines_x, key=lambda x: abs(mx - x))
        if abs(mx - nearest_x) < 15:
            pygame.draw.line(screen, (0, 128, 255), start_point, (nearest_x, my), 2)

    # Pipes
    for rect, color in pipes:
        pygame.draw.rect(screen, color, rect)

    # Mario
    pygame.draw.rect(screen, (255, 0, 0), (mario_x, mario_y, MARIO_SIZE, MARIO_SIZE))

    pygame.display.flip()

pygame.quit()
sys.exit()