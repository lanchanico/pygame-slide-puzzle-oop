import pygame
import sys

anim_time = 500

screen = pygame.display.set_mode((800, 400))

count = 0.0
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                pygame.quit()
                sys.exit()
    
    print(pygame.time.get_ticks(), clock.get_fps())

    clock.tick(60)
