import pygame
import sys
import os
import math

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
SLIDE_SPEED = 2

PIPE_Y = WINDOW_HEIGHT - 40
MAX_PATH_LENGTH = WINDOW_HEIGHT // 2
MUSIC_FOLDER = "music/"
SOUNDS_FOLDER = "sounds/"
MAIN_MUSIC = MUSIC_FOLDER + "slides.mp3"
SOUND_PATH = SOUNDS_FOLDER + "scream.mp3"
WIN_SOUND_PATH = SOUNDS_FOLDER + "win.mp3"
DRAW_SOUND_PATH = SOUNDS_FOLDER + "line_drawing.mp3"
SNAP_SOUND_PATH = SOUNDS_FOLDER + "line_snap.mp3"

# --- Assets ---
scream_sound = pygame.mixer.Sound(SOUND_PATH) if os.path.exists(SOUND_PATH) else None
win_sound = pygame.mixer.Sound(WIN_SOUND_PATH) if os.path.exists(WIN_SOUND_PATH) else None
draw_sound = pygame.mixer.Sound(DRAW_SOUND_PATH) if os.path.exists(DRAW_SOUND_PATH) else None
snap_sound = pygame.mixer.Sound(SNAP_SOUND_PATH) if os.path.exists(SNAP_SOUND_PATH) else None

# --- Setup ---
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mario's Slides")
clock = pygame.time.Clock()

def play_music():
    if os.path.exists(MAIN_MUSIC):
        pygame.mixer.music.load(MAIN_MUSIC)
        pygame.mixer.music.play(-1)

def reset_game():
    global lines_x, mario_x, mario_y, mario_sliding, slide_target, slide_vector, pipes, drawing, start_point, paths, game_over
    play_music()
    lines_x = [LINE_SPACING * (i + 1) for i in range(LINE_COUNT)]
    mario_x = lines_x[0] - MARIO_SIZE // 2
    mario_y = 0
    mario_sliding = False
    slide_target = None
    slide_vector = (0, 0)
    pipes = []
    for i, x in enumerate(lines_x):
        rect = pygame.Rect(x - 10, PIPE_Y, 20, 20)
        color = (255, 255, 0) if i == LINE_COUNT - 1 else (0, 255, 0)
        pipes.append((rect, color))
    drawing = False
    start_point = None
    paths = []
    game_over = False

# --- Initialize game state ---
reset_game()

# --- Main Loop ---
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = pygame.mouse.get_pos()
            nearest_x = min(lines_x, key=lambda x: abs(mx - x))
            if abs(mx - nearest_x) < 15:
                snapped_y = round(my / 10) * 10
                start_point = (nearest_x, snapped_y)
                drawing = True
                if draw_sound:
                    draw_sound.play(-1)

        if event.type == pygame.MOUSEBUTTONUP and drawing:
            mx, my = pygame.mouse.get_pos()
            nearest_x = min(lines_x, key=lambda x: abs(mx - x))
            if abs(mx - nearest_x) < 15:
                snapped_y = round(my / 10) * 10
                end_point = (nearest_x, snapped_y)
                if start_point[0] != end_point[0]:
                    idx1 = lines_x.index(start_point[0])
                    idx2 = lines_x.index(end_point[0])
                    if abs(idx1 - idx2) == 1:
                        dy = abs(end_point[1] - start_point[1])
                        if dy > MAX_PATH_LENGTH:
                            direction = 1 if end_point[1] > start_point[1] else -1
                            end_point = (end_point[0], start_point[1] + direction * MAX_PATH_LENGTH)
                        valid = True
                        for existing_start, existing_end in paths:
                            if existing_start[1] == start_point[1] and existing_end[1] == end_point[1]:
                                valid = False
                                break
                        if valid:
                            paths.append((start_point, end_point))
                            if snap_sound:
                                snap_sound.play()
            drawing = False
            start_point = None
            if draw_sound:
                draw_sound.stop()

    if not game_over:
        if mario_sliding:
            mario_x += slide_vector[0] * SLIDE_SPEED
            mario_y += slide_vector[1] * SLIDE_SPEED
            dx = slide_target[0] - mario_x
            dy = slide_target[1] - mario_y
            if dx * slide_vector[0] <= 0 and dy * slide_vector[1] <= 0:
                mario_x, mario_y = slide_target
                mario_sliding = False
        else:
            mario_y += MARIO_SPEED
            mario_center = (mario_x + MARIO_SIZE // 2, mario_y + MARIO_SIZE)
            for start, end in paths:
                min_y = min(start[1], end[1])
                max_y = max(start[1], end[1])
                path_mid_y = (start[1] + end[1]) // 2
                if abs(mario_center[1] - path_mid_y) <= MARIO_SPEED:
                    current_line = min(lines_x, key=lambda x: abs(mario_center[0] - x))
                    if current_line == start[0]:
                        mario_sliding = True
                        slide_target = (end[0] - MARIO_SIZE // 2, end[1])
                        dx = slide_target[0] - mario_x
                        dy = slide_target[1] - mario_y
                        length = math.hypot(dx, dy)
                        slide_vector = (dx / length, dy / length)
                        break

        for rect, color in pipes:
            if rect.collidepoint(mario_x + MARIO_SIZE // 2, mario_y + MARIO_SIZE):
                if color == (255, 255, 0):
                    if win_sound:
                        win_sound.play()
                    game_over = True
                else:
                    if scream_sound:
                        scream_sound.play()
                    game_over = True

    screen.fill((0, 0, 0))

    for x in lines_x:
        pygame.draw.line(screen, (255, 255, 255), (x, 0), (x, WINDOW_HEIGHT), 2)

    for start, end in paths:
        pygame.draw.line(screen, (0, 255, 255), start, end, 3)

    if drawing and start_point:
        mx, my = pygame.mouse.get_pos()
        nearest_x = min(lines_x, key=lambda x: abs(mx - x))
        if abs(mx - nearest_x) < 15:
            snapped_y = round(my / 10) * 10
            pygame.draw.line(screen, (0, 128, 255), start_point, (nearest_x, snapped_y), 2)

    for rect, color in pipes:
        pygame.draw.rect(screen, color, rect)

    pygame.draw.rect(screen, (255, 0, 0), (mario_x, mario_y, MARIO_SIZE, MARIO_SIZE))

    pygame.display.flip()

pygame.quit()
sys.exit()
