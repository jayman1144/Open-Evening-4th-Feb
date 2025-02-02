import pygame
import random
import sys

SCREEN_WIDTH, SCREEN_HEIGHT = 700, 600
ICON_SIZE = (100, 100)
REEL_POSITIONS = [150, 300, 450]
ROW_Y_POSITIONS = [150, 250, 350]
SPIN_DURATION = 3000  
ACCELERATION = 0.3   
DECELERATION = 0.5    
FPS = 60
MAX_SPIN_SPEED = 15
STOP_DELAY = 200  #delay between reel stops
SCORE_PER_WIN = 100  

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Slot Machine")

#easing functions for slowing animations (definitely dont want to change these)
def ease_out_quad(t):
    return t * (2 - t)

def ease_in_out_quad(t):
    return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t


def load_and_resize_image(file_path, size):
    try:
        image = pygame.image.load(file_path)
        return pygame.transform.scale(image, size)
    except pygame.error as e:
        print(f"Error loading image: {file_path}")
        sys.exit()

icon = load_and_resize_image('slot-machine.png', (32, 32))
pygame.display.set_icon(icon)

seven_img = load_and_resize_image('seven (1).png', ICON_SIZE)
cherries_img = load_and_resize_image('cherries.png', ICON_SIZE)
bars_img = load_and_resize_image('bars.png', ICON_SIZE)

#symbols and reels
symbols = [seven_img, cherries_img, bars_img]
current_reels = [[random.choice(symbols) for _ in range(3)] for _ in range(3)]

#animation variables
class ReelState:
    IDLE = 0
    SPINNING = 1
    STOPPING = 2

reel_states = [ReelState.IDLE for _ in range(3)]
spin_speeds = [0.0 for _ in range(3)]
spin_start_times = [0 for _ in range(3)]

#fonts and win message
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)
win_message = ""
score = 0  

pygame.joystick.init()
joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None

def draw_reels():
    current_time = pygame.time.get_ticks()
    for col in range(3):
        state = reel_states[col]
        base_y = ROW_Y_POSITIONS[0]
        speed = spin_speeds[col]
        
        for row in range(3):
            y_offset = 0
            if state != ReelState.IDLE:
                elapsed = current_time - spin_start_times[col]
                if state == ReelState.SPINNING:
                    progress = min(elapsed / SPIN_DURATION, 1.0)
                    y_offset = ease_in_out_quad(progress) * SCREEN_HEIGHT
                elif state == ReelState.STOPPING:
                    stop_progress = min(elapsed / (SPIN_DURATION * 0.3), 1.0)
                    y_offset = (1 - ease_out_quad(stop_progress)) * SCREEN_HEIGHT
                
                if speed > 5:
                    angle = (current_time % 360) * speed / 10
                    img = pygame.transform.rotate(current_reels[col][row], angle)
                else:
                    img = current_reels[col][row]
            else:
                img = current_reels[col][row]

            final_y = (base_y + row * 100 + y_offset) % SCREEN_HEIGHT
            screen.blit(img, (REEL_POSITIONS[col], final_y))

def start_spin():
    global reel_states, spin_speeds, win_message
    win_message = ""
    for col in range(3):
        reel_states[col] = ReelState.SPINNING
        spin_speeds[col] = 0.0
        spin_start_times[col] = pygame.time.get_ticks() + col * 150  #staggers start of animation

def update_reels():
    current_time = pygame.time.get_ticks()
    for col in range(3):
        if reel_states[col] == ReelState.SPINNING:
            spin_speeds[col] = min(spin_speeds[col] + ACCELERATION, MAX_SPIN_SPEED)
            if current_time > spin_start_times[col] + SPIN_DURATION + col * STOP_DELAY:
                reel_states[col] = ReelState.STOPPING
                spin_start_times[col] = current_time

        elif reel_states[col] == ReelState.STOPPING:
            spin_speeds[col] = max(spin_speeds[col] - DECELERATION, 0)
            if spin_speeds[col] <= 0:
                reel_states[col] = ReelState.IDLE
                current_reels[col] = [random.choice(symbols) for _ in range(3)]

def check_win_condition():
    winning_lines = 0
    for row in range(3):
        if current_reels[0][row] == current_reels[1][row] == current_reels[2][row]:
            winning_lines += 1
    return winning_lines

def draw_score():
    score_text = small_font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH - 150, 20))

running = True
clock = pygame.time.Clock()
while running:
    clock.tick(FPS)
    screen.fill((128, 128, 128))  

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
            if all(state == ReelState.IDLE for state in reel_states):
                start_spin()

    update_reels()
    draw_reels()

    if all(state == ReelState.IDLE for state in reel_states) and not win_message:
        winning_lines = check_win_condition()
        if winning_lines > 0:
            win_message = "YOU WIN!"
            score += winning_lines * SCORE_PER_WIN  #updates score for each line won

    if win_message:
        text_surface = font.render(win_message, True, (255, 215, 0))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surface, text_rect)

    draw_score()  
    pygame.display.update()

pygame.quit()
