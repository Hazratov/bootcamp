import pygame
from pygame import Vector2

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

player_black = Vector2(screen.get_width() / 2, screen.get_height() / 2)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(color="white")

    pygame.draw.circle(screen, (112,112,114),player_black,30)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_black.y -= 300*dt
    if keys[pygame.K_s]:
        player_black.y += 300*dt
    if keys[pygame.K_a]:
        player_black.x -= 300*dt
    if keys[pygame.K_d]:
        player_black.x += 300*dt

    if keys[pygame.K_UP]:
        player_black.y -= 300*dt
    if keys[pygame.K_DOWN]:
        player_black.y += 300*dt
    if keys[pygame.K_LEFT]:
        player_black.x -= 300*dt
    if keys[pygame.K_RIGHT]:
        player_black.x += 300*dt



    pygame.display.flip()
    dt = clock.tick(60) / 1000

pygame.quit()

