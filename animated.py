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
STOP_DELAY = 200
SCORE_PER_WIN = 100
HIGHLIGHT_COLOR = (255, 215, 0)
INPUT_COOLDOWN = 200 #prevents odd ignoring of inputs (not entirely sure why this happens but ik that it does)
INITIAL_SCORE = 100
BASE_SPIN_COST = 20


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Slot Machine")


pygame.mixer.init()
pygame.mixer.set_num_channels(3)  #separate channels for music and sound effects


spin_sound = pygame.mixer.Sound("spin.wav")
win_sound = pygame.mixer.Sound("win.wav")


pygame.mixer.music.load("background_music.mp3")  
pygame.mixer.music.set_volume(0.3)  #volume adjusted between 0.0 and 1.0
pygame.mixer.music.play(-1)

#fonts
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

#easing functions
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

#game state is here to handle instances when score <= 0 or when the spin cost exceeds the current score 
#there is a slight issue with the latter fail state but seems relatively simple to fix 
class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.score = INITIAL_SCORE
        self.win_message = ""
        self.winning_rows = []
        self.game_over = False
        self.game_over_time = 0
        self.current_spin_cost = BASE_SPIN_COST
        self.current_reels = [[random.choice(symbols) for _ in range(3)] for _ in range(3)]
        self.reel_states = [ReelState.IDLE for _ in range(3)]
        self.spin_speeds = [0.0 for _ in range(3)]
        self.spin_start_times = [0 for _ in range(3)]

class ReelState:
    IDLE = 0
    SPINNING = 1
    STOPPING = 2

game_state = GameState()

#checks for issues with controller to prevent aforementioned soft locking 
class JoystickManager:
    def __init__(self):
        self.joystick = None
        self.should_quit = False
        self.last_input_time = 0
        self.init_joystick()

    def init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print(f"Joystick connected: {self.joystick.get_name()}")
            except Exception as e:
                print(f"Joystick connection error: {str(e)}")
                self.joystick = None
        else:
            self.joystick = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.should_quit = True
            elif event.type == pygame.JOYDEVICEADDED:
                self.init_joystick()
            elif event.type == pygame.JOYDEVICEREMOVED:
                print("Joystick disconnected")
                self.joystick = None
            elif event.type == pygame.JOYBUTTONDOWN:
                now = pygame.time.get_ticks()
                if event.button == 0 and now - self.last_input_time > INPUT_COOLDOWN:
                    self.last_input_time = now
                    if all(state == ReelState.IDLE for state in game_state.reel_states):
                        if game_state.score >= game_state.current_spin_cost and not game_state.game_over:
                            start_spin()

#applies animations to each icon 
def draw_reels():
    current_time = pygame.time.get_ticks()
    for col in range(3):
        state = game_state.reel_states[col]
        base_y = ROW_Y_POSITIONS[0]
        speed = game_state.spin_speeds[col]
        
        for row in range(3):
            y_offset = 0
            if state != ReelState.IDLE:
                elapsed = current_time - game_state.spin_start_times[col]

                if state == ReelState.SPINNING:
                    progress = min(elapsed / SPIN_DURATION, 1.0)
                    y_offset = ease_in_out_quad(progress) * SCREEN_HEIGHT

                elif state == ReelState.STOPPING:
                    stop_progress = min(elapsed / (SPIN_DURATION * 0.3), 1.0)
                    y_offset = (1 - ease_out_quad(stop_progress)) * SCREEN_HEIGHT
                
                if speed > 5:
                    angle = (current_time % 360) * speed / 10
                    img = pygame.transform.rotate(game_state.current_reels[col][row], angle)
                else:
                    img = game_state.current_reels[col][row]
            else:
                img = game_state.current_reels[col][row]

            final_y = (base_y + row * 100 + y_offset) % SCREEN_HEIGHT
            screen.blit(img, (REEL_POSITIONS[col], final_y))

def draw_winning_highlights():
    for row in game_state.winning_rows:
        x = REEL_POSITIONS[0]
        y = ROW_Y_POSITIONS[row]
        width = REEL_POSITIONS[2] + ICON_SIZE[0] - x
        height = ICON_SIZE[1]
        
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
        glow_thickness = int(3 + pulse * 2)
        
        pygame.draw.rect(
            screen,
            HIGHLIGHT_COLOR,
            (x - 2, y - 2, width + 4, height + 4),
            glow_thickness,
            border_radius=5
        )
#checks for changes in game state at start of spin 
# which causes the issue with the latter fail state as it is checking on the first frame after input is detected
def start_spin():
    game_state.win_message = ""
    game_state.winning_rows = []
    game_state.score -= game_state.current_spin_cost
    
    #immediate game over check after spending
    if game_state.score < 0 or game_state.current_spin_cost > game_state.score:
        game_state.game_over = True
        game_state.game_over_time = pygame.time.get_ticks()
        return
    
    for col in range(3):
        game_state.reel_states[col] = ReelState.SPINNING
        game_state.spin_speeds[col] = 0.0
        game_state.spin_start_times[col] = pygame.time.get_ticks() + col * 150
    
    spin_sound.play()

def update_reels():
    current_time = pygame.time.get_ticks()
    for col in range(3):
        if game_state.reel_states[col] == ReelState.SPINNING:
            game_state.spin_speeds[col] = min(game_state.spin_speeds[col] + ACCELERATION, MAX_SPIN_SPEED)

            if current_time > game_state.spin_start_times[col] + SPIN_DURATION + col * STOP_DELAY:
                game_state.reel_states[col] = ReelState.STOPPING
                game_state.spin_start_times[col] = current_time

        elif game_state.reel_states[col] == ReelState.STOPPING:
            game_state.spin_speeds[col] = max(game_state.spin_speeds[col] - DECELERATION, 0)
            if game_state.spin_speeds[col] <= 0:
                game_state.reel_states[col] = ReelState.IDLE
                game_state.current_reels[col] = [random.choice(symbols) for _ in range(3)]

def check_win_condition():
    winning = []
    for row in range(3):
        if game_state.current_reels[0][row] == game_state.current_reels[1][row] == game_state.current_reels[2][row]:
            winning.append(row)
    return winning

def draw_score():
    score_text = small_font.render(
        f"Score: {game_state.score} (Next Spin: {game_state.current_spin_cost})", 
        True, 
        (255, 255, 255)
    )
    screen.blit(score_text, (SCREEN_WIDTH - 350, 20))

def main():
    clock = pygame.time.Clock()
    joy_manager = JoystickManager()

    #starts background music
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play(-1)

    while not joy_manager.should_quit:
        clock.tick(FPS)
        screen.fill((128, 128, 128))

        #restarts music if it stops (e.g., after game reset)
        if not pygame.mixer.music.get_busy() and not game_state.game_over:
            pygame.mixer.music.play(-1)

        if game_state.game_over:
            screen.fill((0, 0, 0))
            game_over_text = font.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)
            pygame.display.update()
            
            if pygame.time.get_ticks() - game_state.game_over_time >= 3000:
                game_state.reset()
            continue

        joy_manager.handle_events()
        update_reels()
        draw_reels()

        if all(state == ReelState.IDLE for state in game_state.reel_states) and not game_state.win_message:
            game_state.winning_rows = check_win_condition()
            if game_state.winning_rows:
                game_state.win_message = "YOU WIN!"
                game_state.score += len(game_state.winning_rows) * SCORE_PER_WIN
                game_state.current_spin_cost *= 2
                win_sound.play()
                
                
                if game_state.current_spin_cost > game_state.score:
                    game_state.game_over = True
                    game_state.game_over_time = pygame.time.get_ticks()

        #continuously checks for game over 
        if game_state.score <= 0 or game_state.current_spin_cost > game_state.score:
            game_state.game_over = True
            game_state.game_over_time = pygame.time.get_ticks()

        if game_state.winning_rows and all(state == ReelState.IDLE for state in game_state.reel_states):
            draw_winning_highlights()
        
        if game_state.win_message:
            text_surface = font.render(game_state.win_message, True, HIGHLIGHT_COLOR)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(text_surface, text_rect)

        draw_score()
        pygame.display.update()

    pygame.mixer.music.stop()
    pygame.quit()

if __name__ == "__main__":
    main()