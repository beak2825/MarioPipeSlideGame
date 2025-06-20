import pygame
import sys
import os
import math
import time

# --- Init ---
pygame.init()

# --- Constants ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

LINE_COUNT = 4
LINE_SPACING = 80

MARIO_SIZE = 20
MARIO_SPEED = 1.1
SLIDE_SPEED = 2

PIPE_Y = WINDOW_HEIGHT - 40
MAX_PATH_LENGTH = WINDOW_HEIGHT // 10
MUSIC_FOLDER = "music/"
SOUNDS_FOLDER = "sounds/"
MAIN_MUSIC = MUSIC_FOLDER + "slides.mp3"
SOUND_PATH = SOUNDS_FOLDER + "scream.mp3"
WIN_SOUND_PATH = SOUNDS_FOLDER + "win.mp3"
DRAW_SOUND_PATH = SOUNDS_FOLDER + "line_drawing.mp3"
SNAP_SOUND_PATH = SOUNDS_FOLDER + "line_snap.mp3"
POP_SOUND_PATH = SOUNDS_FOLDER + "mario_pop.mp3"

# --- Configurable Mario Start VLINE ---
MARIO_START_VLINE = 0  # 0 = VLINE 1, 1 = VLINE 2, etc.
VLINE_STAR = 4  # 1-based index for user, will convert to 0-based
RANDOMIZE_STAR_LOCATION = False

# --- Assets ---
scream_sound = pygame.mixer.Sound(SOUND_PATH) if os.path.exists(SOUND_PATH) else None
win_sound = pygame.mixer.Sound(WIN_SOUND_PATH) if os.path.exists(WIN_SOUND_PATH) else None
draw_sound = pygame.mixer.Sound(DRAW_SOUND_PATH) if os.path.exists(DRAW_SOUND_PATH) else None
snap_sound = pygame.mixer.Sound(SNAP_SOUND_PATH) if os.path.exists(SNAP_SOUND_PATH) else None
pop_sound = pygame.mixer.Sound(POP_SOUND_PATH) if os.path.exists(POP_SOUND_PATH) else None

# --- Setup ---
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mario's Slides")
clock = pygame.time.Clock()

# --- Game State Variables ---
VLINE_STATE = [0] * LINE_COUNT
PATH = 0
VLINE_PERCENTAGE = 0
ABOUT_TO_DIE = 1
ABOUT_TO_WIN = 0
DIST_NEXT_PATH = 0
SEC_ALIVE = 0.00
start_time = 0.0
used_paths = set()  # Track used paths for sliding


def play_music():
    if os.path.exists(MAIN_MUSIC):
        pygame.mixer.music.load(MAIN_MUSIC)
        pygame.mixer.music.play(-1)


def reset_game():
    global lines_x, mario_x, mario_y, mario_sliding, pipes, drawing, start_point, paths
    global game_over, slide_target, prev_path, start_time, SEC_ALIVE, VLINE_STAR
    play_music()
    lines_x = [LINE_SPACING * (i + 1) for i in range(LINE_COUNT)]
    # Randomize star location if enabled
    if RANDOMIZE_STAR_LOCATION:
        import random
        star_idx = random.randint(0, LINE_COUNT - 1)
        VLINE_STAR = star_idx + 1
    else:
        star_idx = VLINE_STAR - 1
    mario_x = lines_x[MARIO_START_VLINE] - MARIO_SIZE // 2
    mario_y = 0
    mario_sliding = False
    slide_target = None
    prev_path = None
    pipes = []
    for i, x in enumerate(lines_x):
        # Place star at VLINE_STAR, piranha at others
        color = (255, 255, 0) if i == star_idx else (0, 255, 0)
        rect = pygame.Rect(x - 10, PIPE_Y, 20, 20)
        pipes.append((rect, color))
    drawing = False
    start_point = None
    paths = []
    game_over = False
    start_time = time.time()
    SEC_ALIVE = 0.00


reset_game()

running = True
while running:
    clock.tick(FPS)

    if not game_over:
        SEC_ALIVE = round(time.time() - start_time, 2)

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
                # Ensure start_point and end_point are not None before using
                if start_point is not None and end_point is not None and start_point[0] != end_point[0]:
                    idx1 = lines_x.index(start_point[0])
                    idx2 = lines_x.index(end_point[0])
                    if abs(idx1 - idx2) == 1:
                        dy = abs(end_point[1] - start_point[1])
                        if dy > MAX_PATH_LENGTH:
                            direction = 1 if end_point[1] > start_point[1] else -1
                            end_point = (end_point[0], start_point[1] + direction * MAX_PATH_LENGTH)
                        valid = True
                        for existing_start, existing_end in paths:
                            sy1, sy2 = sorted([existing_start[1], existing_end[1]])
                            ey1, ey2 = sorted([start_point[1], end_point[1]])
                            if (sy1 <= ey2 and ey1 <= sy2) and (existing_start[0] in (start_point[0], end_point[0]) or existing_end[0] in (start_point[0], end_point[0])):
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
        mario_center_x = mario_x + MARIO_SIZE // 2
        mario_center_y = mario_y + MARIO_SIZE // 2
        VLINE_STATE = [0] * LINE_COUNT
        PATH = 1 if mario_sliding else 0
        VLINE_PERCENTAGE = min(100, int((mario_y / (PIPE_Y)) * 100))
        ABOUT_TO_DIE = 1
        ABOUT_TO_WIN = 0
        DIST_NEXT_PATH = 100
        for i, x in enumerate(lines_x):
            if abs(mario_center_x - x) < 5:
                VLINE_STATE[i] = 1
                mario_vline_idx = i
                break
        else:
            mario_vline_idx = None

        # --- ABOUT_TO_DIE and ABOUT_TO_WIN logic ---
        path_below = False
        min_path_y = None
        next_path_dist = None
        if mario_vline_idx is not None:
            for start, end in paths:
                if start[0] == end[0]:
                    continue
                # Only consider paths on Mario's VLINE
                if (start[0] == lines_x[mario_vline_idx] or end[0] == lines_x[mario_vline_idx]):
                    path_y = start[1]
                    if path_y > mario_y + MARIO_SIZE // 2:
                        path_below = True
                        dist = path_y - (mario_y + MARIO_SIZE // 2)
                        if next_path_dist is None or dist < next_path_dist:
                            next_path_dist = dist
                        if min_path_y is None or path_y < min_path_y:
                            min_path_y = path_y
        if path_below:
            ABOUT_TO_DIE = 0
        if mario_sliding:
            ABOUT_TO_DIE = 0
        star_idx = VLINE_STAR - 1
        if mario_vline_idx == star_idx:
            ABOUT_TO_DIE = 0
            max_path_y = -1
            for start, end in paths:
                if (start[0] == lines_x[star_idx] or end[0] == lines_x[star_idx]):
                    path_y = start[1]
                    if path_y > max_path_y:
                        max_path_y = path_y
            if mario_y + MARIO_SIZE // 2 > max_path_y:
                ABOUT_TO_WIN = 1
        if path_below and mario_vline_idx == star_idx:
            ABOUT_TO_WIN = 0
        # --- DIST_NEXT_PATH logic ---
        if next_path_dist is not None:
            DIST_NEXT_PATH = int(next_path_dist)
        else:
            # If Mario is below all paths on his VLINE, set to -1
            DIST_NEXT_PATH = -1
        # --- Used paths logic ---
        if mario_y <= 0:
            used_paths.clear()
        # --- Smooth sliding logic with used paths ---
        if mario_sliding:
            dx = slide_target[0] - mario_x
            dy = slide_target[1] - mario_y
            dist = math.hypot(dx, dy)
            if dist <= MARIO_SPEED:
                mario_x = slide_target[0]
                mario_y = slide_target[1]
                mario_sliding = False
            else:
                step_x = MARIO_SPEED * (dx / dist)
                step_y = MARIO_SPEED * (dy / dist)
                mario_x += step_x
                mario_y += step_y
        else:
            hopped = False
            for start, end in paths:
                path_id = tuple(sorted([start, end]))
                for px, py in [start, end]:
                    if (
                        abs(mario_center_x - px) < MARIO_SIZE // 2 and
                        abs((mario_y + MARIO_SIZE // 2) - py) < MARIO_SPEED and
                        path_id not in used_paths
                    ):
                        other = end if (px, py) == start else start
                        slide_target = (other[0] - MARIO_SIZE // 2, other[1] - MARIO_SIZE // 2)
                        mario_sliding = True
                        used_paths.add(path_id)
                        if pop_sound: pop_sound.play()
                        hopped = True
                        break
                if hopped:
                    break
            if not hopped:
                mario_y += MARIO_SPEED
        # --- Death check: if Mario falls past the last path and not on a VLINE with a path, he dies ---
        if mario_y + MARIO_SIZE >= PIPE_Y:
            # If not on star, it's a loss
            star_x = lines_x[VLINE_STAR - 1]
            if abs(mario_center_x - star_x) < 5:
                for rect, color in pipes:
                    if color == (255, 255, 0) and rect.top - mario_y < 5:
                        if win_sound: win_sound.play()
                        game_over = True
            else:
                if scream_sound: scream_sound.play()
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

    font = pygame.font.SysFont(None, 20)
    debug = [
        f"VLINE_1 = {VLINE_STATE[0]}",
        f"VLINE_2 = {VLINE_STATE[1]}",
        f"VLINE_3 = {VLINE_STATE[2]}",
        f"VLINE_4 = {VLINE_STATE[3]}",
        f"PATH = {PATH}",
        f"VLINE_PERCENTAGE = {VLINE_PERCENTAGE} pixels",
        f"ABOUT_TO_DIE = {ABOUT_TO_DIE}",
        f"ABOUT_TO_WIN = {ABOUT_TO_WIN}",
        f"DIST_NEXT_PATH = {DIST_NEXT_PATH}%",
        f"SEC_ALIVE = {SEC_ALIVE:.2f}"
    ]
    for i, txt in enumerate(debug):
        render = font.render(txt, True, (255, 255, 255))
        screen.blit(render, (420, 10 + i * 20))

    pygame.display.flip()

pygame.quit()
sys.exit()
