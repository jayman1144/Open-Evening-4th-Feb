import pygame
import random

pygame.init()

screen_width, screen_height = 700, 600
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN) 
pygame.display.set_caption("Slot Machine")
icon = pygame.image.load('slot-machine.png')
pygame.display.set_icon(icon)

#re-sizes the 32x32 icons
def load_and_resize_image(file_path, size):
    image = pygame.image.load(file_path)
    return pygame.transform.scale(image, size)

icon_size = (100, 100)  

seven_img = load_and_resize_image('seven (1).png', icon_size)
cherries_img = load_and_resize_image('cherries.png', icon_size)
bars_img = load_and_resize_image('bars.png', icon_size)

# Initial positions for three columns
symbols = [seven_img, cherries_img, bars_img]
reel_positions = [150, 300, 450] 
row_y_positions = [150, 250, 350]  
current_reels = [[random.choice(symbols) for _ in range(3)] for _ in range(3)]  #initialses with random symbols
spinning = False
spin_time = 0

#animation stuff that almost made my head spin when making it, hence why the animations are 'good enough' and not perfect
spin_duration = 3000  
frame_duration = 50  #duration for each frame in milliseconds
frames_per_spin = spin_duration // frame_duration  #total frames for spinning
spin_index = 0  #used for frame indexing
returning = False  
return_index = 0  
return_duration = 600  
frames_per_return = return_duration // frame_duration  #total frames for returning


font = pygame.font.Font(None, 74)  
win_message = ""  

def draw_reels(reel_symbols):
    for col in range(3):
        for row in range(3):
            # Calculate the y position for spinning or returning
            if returning:
                # Calculate the return position
                y_pos = row_y_positions[row] + ((spin_index * 5 + return_index * 5) % screen_height)
            else:
                # Normal spin position
                y_pos = (row_y_positions[row] + (spin_index * 5)) % screen_height
            
            screen.blit(reel_symbols[col][row], (reel_positions[col], y_pos))

def spin_reels():
    global spinning, spin_time, spin_index, returning, return_index, win_message
    spinning = True
    spin_time = 0
    spin_index = 0
    returning = False
    win_message = ""  
    #generate new symbols for the last position
    for col in range(3):
        current_reels[col] = [random.choice(symbols) for _ in range(3)]

def check_win_condition():
    
    for row in range(3):
        if current_reels[0][row] == current_reels[1][row] == current_reels[2][row]:
            return True

    
    # for col in range(3):
    #     if current_reels[col][0] == current_reels[col][1] == current_reels[col][2]:
    #         return True 
    #commented out for now as leaving it in in current form caused probability of winning to be 80%
    #was useful for testing but may not be in final 
    
    return False

def update_reels():
    global spin_time, spinning, spin_index, returning, return_index
    if spinning:
        spin_time += frame_duration
        spin_index += 1
        
        #stop spinning after the total number of frames
        if spin_index >= frames_per_spin:
            spinning = False
            returning = True  #begins returning animation
            spin_index = 0  

    if returning:
        return_index += 1
        #stop returning after the total number of frames
        if return_index >= frames_per_return:
            returning = False
            return_index = 0  

#initialises controller
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)  
joystick.init()

running = True
clock = pygame.time.Clock()
while running:
    clock.tick(60)  #limit to 60 fps(especially important for animations)
    screen.fill((128, 128, 128)) #sets RGB values for background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        #checks for button with index 0 (typically 'x' button though may not be on the arcade machine) which 
        # almost certainly exists on arcade machine
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  
                spin_reels()  

    
    update_reels()

    #assigns new positions
    draw_reels(current_reels)

    #checks for win condition after returning to the original position
    if not spinning and not returning:
        win = check_win_condition()
        if win:
            win_message = f"You win!"  #win message uses an f string as i was going to include the symbol which
                                        #caused the win but this became a pain so was removed for now
    #renders win message
    if win_message:
        text_surface = font.render(win_message, True, (255, 215, 0))  #gold color for win message
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(text_surface, text_rect)  
    #updates the display every frame
    pygame.display.update()

pygame.quit()
