import pygame
import time

pygame.mixer.init()

def background_music_loop(path, delay):
    pygame.mixer.music.load(path)
    check_length = pygame.mixer.Sound(path)

    while True:
        pygame.mixer.music.play()
        time.sleep(check_length.get_length() + delay)


# This is just test code
# background_music_loop('music/luigi_casino.mp3', 2)

