import pygame
import sys
import os
import math
import time
import random
import json

# --- Init ---
pygame.init()

# --- Constants ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

LINE_COUNT = 4
LINE_SPACING = 80

MARIO_SIZE = 20
MARIO_SPEED_DEFAULT = 1.1
MARIO_SPEED_FAST = MARIO_SPEED_DEFAULT * 4
MARIO_SPEED = MARIO_SPEED_DEFAULT
SLIDE_SPEED = 2

PIPE_Y = WINDOW_HEIGHT - 40
MAX_PATH_LENGTH = WINDOW_HEIGHT // 10
MUSIC_FOLDER = "music/"
SOUNDS_FOLDER = "sounds/"
SPRITES_FOLDER = "sprites/"
# --- Sound Paths ---
MAIN_MUSIC = MUSIC_FOLDER + "slides.mp3" # Plays whole time
SOUND_PATH = SOUNDS_FOLDER + "scream.mp3" # plays on death
WIN_SOUND_PATH = SOUNDS_FOLDER + "win.mp3"
DRAW_SOUND_PATH = SOUNDS_FOLDER + "line_drawing.mp3"
SNAP_SOUND_PATH = SOUNDS_FOLDER + "line_snap.mp3"
POP_SOUND_PATH = SOUNDS_FOLDER + "mario_pop.mp3"
SPEEDUP_SOUND_PATH = SOUNDS_FOLDER + "speedUp.mp3"

# --- Sprites ---
SPRITE_MARIO_PATH = SPRITES_FOLDER + "mario.png"
SPRITE_STAR_PATH = SPRITES_FOLDER + "star.png"
SPRITE_PIPE_PATH = SPRITES_FOLDER + "pipe.png"
SPRITE_PIRANHA_PATH = SPRITES_FOLDER + "piranha.png"



# --- Configurable Mario Start VLINE ---
MARIO_SIZE = 32
STAR_SIZE = 16
MARIO_START_VLINE = 0  # 0 = VLINE 1, 1 = VLINE 2, etc.
VLINE_STAR = None # 1-based index for user, will convert to 0-based
RANDOMIZE_STAR_LOCATION = False


# Load images as Surfaces
SPRITE_MARIO = pygame.image.load(SPRITE_MARIO_PATH) if os.path.exists(SPRITE_MARIO_PATH) else pygame.Surface((MARIO_SIZE, MARIO_SIZE))
SPRITE_STAR = pygame.image.load(SPRITE_STAR_PATH) if os.path.exists(SPRITE_STAR_PATH) else pygame.Surface((STAR_SIZE, STAR_SIZE))
SPRITE_PIPE = pygame.image.load(SPRITE_PIPE_PATH) if os.path.exists(SPRITE_PIPE_PATH) else pygame.Surface((20, 20))
SPRITE_PIRANHA = pygame.image.load(SPRITE_PIRANHA_PATH) if os.path.exists(SPRITE_PIRANHA_PATH) else pygame.Surface((20, 20))

# --- Assets ---
scream_sound = pygame.mixer.Sound(SOUND_PATH) if os.path.exists(SOUND_PATH) else None
win_sound = pygame.mixer.Sound(WIN_SOUND_PATH) if os.path.exists(WIN_SOUND_PATH) else None
draw_sound = pygame.mixer.Sound(DRAW_SOUND_PATH) if os.path.exists(DRAW_SOUND_PATH) else None
snap_sound = pygame.mixer.Sound(SNAP_SOUND_PATH) if os.path.exists(SNAP_SOUND_PATH) else None
pop_sound = pygame.mixer.Sound(POP_SOUND_PATH) if os.path.exists(POP_SOUND_PATH) else None
speedup_sound = pygame.mixer.Sound(SPEEDUP_SOUND_PATH) if os.path.exists(SPEEDUP_SOUND_PATH) else None

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
TIME_TO_WIN = None
start_time = 0.0
used_webs = set()  # Track used webs for sliding
websAmount = 0
STAR_IDX = None  # 0-based index for star sprite location
wonGames = 0  # Track number of games won
waiting_for_win_sound = False  # Track if waiting for win sound to finish
win_sound_end_time = 0


def save_web_map(filename="webMap.json"):
    try:
        # Save as a list of [[x1, y1], [x2, y2]] for each web
        web_list = [[list(start), list(end)] for start, end in webs]
        with open(filename, "w") as f:
            json.dump(web_list, f, indent=2)
        print(f"Web map saved to {filename}")
    except Exception as e:
        print(f"Error saving web map: {e}")

def load_web_map(filename="webMap.json"):
    global webs, websAmount
    try:
        with open(filename, "r") as f:
            web_list = json.load(f)
        webs = [ (tuple(start), tuple(end)) for start, end in web_list ]
        websAmount = len(webs)
        print(f"Web map loaded from {filename}")
    except Exception as e:
        print(f"Error loading web map: {e}")


def play_music():
    if os.path.exists(MAIN_MUSIC):
        pygame.mixer.music.load(MAIN_MUSIC)
        pygame.mixer.music.play(-1)


def reset_game():
    global lines_x, mario_x, mario_y, mario_sliding, pipes, drawing, start_point, webs
    global game_over, slide_target, prev_path, start_time, SEC_ALIVE, VLINE_STAR, websAmount, TIME_TO_WIN
    global STAR_IDX, waiting_for_win_sound, win_sound_end_time
    if 'webs' not in globals():
        webs = []
    play_music()
    lines_x = [LINE_SPACING * (i + 1) for i in range(LINE_COUNT)]

    VLINE_STAR = random.randint(1, LINE_COUNT)  # 1-based index for win VLINE
    STAR_IDX = VLINE_STAR - 1  # Star sprite always matches the win VLINE
    mario_x = lines_x[random.randint(0, LINE_COUNT - 1)] - MARIO_SIZE // 2  # Random VLINE for Mario
    mario_y = 0
    mario_sliding = False
    slide_target = None
    prev_path = None
    pipes = []
    for i, x in enumerate(lines_x):
        color = (255, 255, 0) if i == STAR_IDX else (0, 255, 0)
        rect = pygame.Rect(x - 10, PIPE_Y, 20, 20)
        pipes.append((rect, color))
    drawing = False
    start_point = None
    game_over = False
    start_time = time.time()
    SEC_ALIVE = 0.00
    TIME_TO_WIN = None
    waiting_for_win_sound = False
    win_sound_end_time = 0
    # Only clear webs if less than 3 wins and webs was not just loaded
    if wonGames < 3 and not getattr(reset_game, 'skip_webs_clear', False):
        webs.clear()
        websAmount = 0

    if wonGames == 3: # Equivalent to rounds getting progressively harder. Also wongames being 3 means that this won't run ever again.
        webs.clear()
        load_web_map("3_Round_webMap.json")
    elif wonGames == 5:  # After 5 wins, load a different web map
        webs.clear()
        load_web_map("5_Round_webMap.json")
    elif wonGames == 10:  # After 10 wins, load a different web map
        webs.clear()
        load_web_map("10_Round_webMap.json")
    # After 3 wins, do NOT clear webs, so they persist
    # Reset the skip_webs_clear flag
    if hasattr(reset_game, 'skip_webs_clear'):
        delattr(reset_game, 'skip_webs_clear')



reset_game()

running = True
while running:
    clock.tick(FPS)

    if waiting_for_win_sound:
        if time.time() >= win_sound_end_time:
            waiting_for_win_sound = False
            reset_game()
        continue

    if not game_over:
        SEC_ALIVE = round(time.time() - start_time, 2)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
            elif event.key == pygame.K_k:
                save_web_map("webMap.json")
            elif event.key == pygame.K_l:
                load_web_map("webMap.json")
                reset_game.skip_webs_clear = True
                reset_game()
            elif event.key == pygame.K_j:
                load_web_map("3_Round_webMap.json")
                reset_game.skip_webs_clear = True
                reset_game()
            elif event.key == pygame.K_u:
                wonGames += 1
            elif event.key == pygame.K_SPACE:
                MARIO_SPEED = MARIO_SPEED_FAST
                if speedup_sound:
                    speedup_sound.play()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                MARIO_SPEED = MARIO_SPEED_DEFAULT

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
                        for existing_start, existing_end in webs:
                            sy1, sy2 = sorted([existing_start[1], existing_end[1]])
                            ey1, ey2 = sorted([start_point[1], end_point[1]])
                            if (sy1 <= ey2 and ey1 <= sy2) and (existing_start[0] in (start_point[0], end_point[0]) or existing_end[0] in (start_point[0], end_point[0])):
                                valid = False
                                break
                        if valid:
                            webs.append((start_point, end_point))
                            websAmount += 1
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
        web_below = False
        min_web_y = None
        next_web_dist = None
        if mario_vline_idx is not None:
            mario_cx = mario_x + MARIO_SIZE // 2
            mario_cy = mario_y + MARIO_SIZE // 2
            for start, end in webs:
                # Only consider webs that span across VLINEs
                x1, y1 = start
                x2, y2 = end
                # Check if Mario's X is between the web's endpoints (inclusive)
                if min(x1, x2) <= mario_cx <= max(x1, x2):
                    # Calculate the Y on the web at Mario's X using linear interpolation
                    if x1 != x2:
                        t = (mario_cx - x1) / (x2 - x1)
                        web_y_at_mario_x = y1 + t * (y2 - y1)
                    else:
                        web_y_at_mario_x = y1  # vertical web
                    if web_y_at_mario_x > mario_cy:
                        web_below = True
                        dist = web_y_at_mario_x - mario_cy
                        if next_web_dist is None or dist < next_web_dist:
                            next_web_dist = dist
                        if min_web_y is None or web_y_at_mario_x < min_web_y:
                            min_web_y = web_y_at_mario_x
        if web_below:
            ABOUT_TO_DIE = 0
        if mario_sliding:
            ABOUT_TO_DIE = 0
        star_idx = (VLINE_STAR - 1) if VLINE_STAR is not None else 0
        if mario_vline_idx == star_idx:
            ABOUT_TO_DIE = 0
            max_web_y = -1
            for start, end in webs:
                if (start[0] == lines_x[star_idx] or end[0] == lines_x[star_idx]):
                    web_y = start[1]
                    if web_y > max_web_y:
                        max_web_y = web_y
            if mario_y + MARIO_SIZE // 2 > max_web_y:
                ABOUT_TO_WIN = 1
        if web_below and mario_vline_idx == star_idx:
            ABOUT_TO_WIN = 0
        # --- DIST_NEXT_WEB logic ---
        if next_web_dist is not None:
            DIST_NEXT_WEB = int(next_web_dist)
        else:
            # If Mario is below all webs on his VLINE, set to -1
            DIST_NEXT_WEB = -1
        # --- Used webs logic ---
        if mario_y <= 0:
            used_webs.clear()
        # --- Smooth sliding logic with used webs ---
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
            mario_cx = mario_x + MARIO_SIZE // 2
            mario_cy = mario_y + MARIO_SIZE // 2
            # --- Improved web detection for high speed ---
            web_hopped_this_frame = False
            if DIST_NEXT_WEB != -1 and ABOUT_TO_DIE == 0 and ABOUT_TO_WIN == 0:
                next_cy = mario_cy + MARIO_SPEED
                for start, end in webs:
                    web_id = tuple(sorted([start, end]))
                    x1, y1 = start
                    x2, y2 = end
                    if min(x1, x2) - 1 <= mario_cx <= max(x1, x2) + 1:
                        dx, dy = x2 - x1, y2 - y1
                        if dx == dy == 0:
                            continue
                        t = max(0, min(1, ((mario_cx - x1) * dx + (mario_cy - y1) * dy) / (dx * dx + dy * dy)))
                        px, py = x1 + t * dx, y1 + t * dy
                        distance = math.hypot(mario_cx - px, mario_cy - py)
                        # --- Symmetric web detection: allow hopping from either endpoint ---
                        if distance < MARIO_SPEED + MARIO_SIZE / 4 and web_id not in used_webs:
                            # Always slide to the endpoint that is NOT closest to Mario's current position
                            if math.hypot(mario_cx - x1, mario_cy - y1) < math.hypot(mario_cx - x2, mario_cy - y2):
                                target = end
                            else:
                                target = start
                            slide_target = (target[0] - MARIO_SIZE // 2, target[1] - MARIO_SIZE // 2)
                            mario_sliding = True
                            used_webs.add(web_id)
                            if pop_sound: pop_sound.play()
                            hopped = True
                            web_hopped_this_frame = True
                            break

            if not hopped and not web_hopped_this_frame:
                mario_y += MARIO_SPEED
        # --- Death check: if Mario falls past the last web and not on a VLINE with a web, he dies ---
        if mario_y + MARIO_SIZE >= PIPE_Y:
            # If not on star, it's a loss
            star_x = lines_x[(VLINE_STAR - 1) if VLINE_STAR is not None else 0]
            if abs(mario_center_x - star_x) < 5:
                for rect, color in pipes:
                    if color == (255, 255, 0) and rect.top - mario_y < 5:
                        if win_sound:
                            win_sound.play()
                            waiting_for_win_sound = True
                            win_sound_end_time = time.time() + win_sound.get_length()
                        game_over = True
                        TIME_TO_WIN = SEC_ALIVE
                        wonGames += 1
            else:
                if scream_sound: scream_sound.play()
                game_over = True

    screen.fill((0, 0, 0))

    for x in lines_x:
        pygame.draw.line(screen, (255, 255, 255), (x, 0), (x, WINDOW_HEIGHT), 2)

    for start, end in webs:
        pygame.draw.line(screen, (0, 255, 255), start, end, 3)

    if drawing and start_point:
        mx, my = pygame.mouse.get_pos()
        nearest_x = min(lines_x, key=lambda x: abs(mx - x))
        if abs(mx - nearest_x) < 15:
            snapped_y = round(my / 10) * 10
            pygame.draw.line(screen, (0, 128, 255), start_point, (nearest_x, snapped_y), 2)

    for i, (rect, color) in enumerate(pipes):
        if i == STAR_IDX:
            # Center the star image in the actual square (rect)
            star_pos = (rect.centerx - SPRITE_STAR.get_width() // 2, rect.centery - SPRITE_STAR.get_height() // 2)
            screen.blit(SPRITE_STAR, star_pos)
        else:
            # is a piranha plant pipe
            # Center the pipe image in the same way as the star
            pipe_pos = (rect.centerx - SPRITE_PIPE.get_width() // 2, rect.centery - SPRITE_PIPE.get_height() // 2)
            screen.blit(SPRITE_PIPE, pipe_pos)

    screen.blit(SPRITE_MARIO, (mario_x, mario_y))

    font = pygame.font.SysFont(None, 20)
    debug = [
        f"VLINE_1 = {VLINE_STATE[0]}",
        f"VLINE_2 = {VLINE_STATE[1]}",
        f"VLINE_3 = {VLINE_STATE[2]}",
        f"VLINE_4 = {VLINE_STATE[3]}",
        f"VLINE_STAR = {VLINE_STAR}",
        f"onWeb = {1 if mario_sliding else 0}",
        f"DIST_NEXT_WEB = {DIST_NEXT_WEB}",
        f"websAmount = {websAmount}",
        f"VLINE_PERCENTAGE = {VLINE_PERCENTAGE} pixels",
        f"ABOUT_TO_DIE = {ABOUT_TO_DIE}",
        f"ABOUT_TO_WIN = {ABOUT_TO_WIN}",
        f"SEC_ALIVE = {SEC_ALIVE:.2f}",
        f"TIME_TO_WIN = {TIME_TO_WIN if TIME_TO_WIN is not None else 0}",
        f"wonGames = {wonGames}",
    ]
    for i, txt in enumerate(debug):
        render = font.render(txt, True, (255, 255, 255))
        screen.blit(render, (420, 10 + i * 20))

    # --- User Notes (lower right, visually distinct, non-blocking) ---
    notes = [
        "SPACE to speed up Mario.",
        "Press K to save your spider-webs.",
        "Press L to load your saved spider-web map.",
        "Press J to load the 3RD Round Map.",
        "Press R to reset the game.",
        "Press U to increase wonGames (for testing).",
    ]
    note_font = pygame.font.SysFont(None, 20, bold=True)
    note_color = (180, 220, 255)
    note_y_start = 10 + len(debug) * 20 + 60  # Many lines below debug
    for i, note in enumerate(notes):
        note_render = note_font.render(note, True, note_color)
        note_rect = note_render.get_rect()
        note_rect.topright = (WINDOW_WIDTH - 10, note_y_start + i * 24)
        screen.blit(note_render, note_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()

