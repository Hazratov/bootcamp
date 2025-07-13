import pygame
from pygame import Vector2

pygame.init()
screen_x, screen_y = 1200, 800
screen = pygame.display.set_mode((screen_x, screen_y))
pygame.display.set_caption("Space Game")
clock = pygame.time.Clock()
running = True

font = pygame.font.Font(None, 36)
bg = pygame.image.load("pictures/background.jpg")
player = pygame.transform.scale(pygame.image.load("pictures/player.png"), [150, 150])
bullet = pygame.transform.scale(pygame.image.load("pictures/bullet.png"), [10, 10])
enemy = pygame.transform.scale(pygame.image.load("pictures/enemy.png"), [200, 150])

#sound
pygame.mixer.init()
bullet_sound = pygame.mixer.Sound("pictures/bullet_sound.wav")

#player
player_x, player_y = 550,620
player_width = player.get_width()
player_height = player.get_height()

#enemy
enemy_x, enemy_y = 100, 10
enemy_width = enemy.get_width()
enemy_height = enemy.get_height()

#bullet
bullets = []
bullet_speed = 10
bullet_with = bullet.get_width()
bullet_height = bullet.get_height()



score = 0
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    text = font.render(f"Score: {score}", True, (255, 255, 255))

    screen.blit(bg, (0,0))
    screen.blit(text, (20, 20))
    screen.blit(player, (player_x, player_y))
    screen.blit(enemy, (enemy_x, enemy_y))

    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_width, enemy_height)
    bullet_rect = pygame.Rect(20,20,bullet_with,bullet_height)


    if player_rect.colliderect(enemy_rect):
        running = False
        print("GAME OVER")

    if bullet_rect.colliderect(enemy_rect):
        score += 1


    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_y -= 20
    if keys[pygame.K_s]:
        player_y += 20
    if keys[pygame.K_a]:
        player_x -= 20
    if keys[pygame.K_d]:
        player_x += 20

    if keys[pygame.K_SPACE]:
        bullets.append({"x": player_x + player_width // 2, "y": player_y})
        bullet_sound.play()


    for bullet_item in bullets:
        bullet_item["y"] -= bullet_speed
        screen.blit(bullet, (bullet_item["x"], bullet_item["y"]))

    bullets = [b for b in bullets if b["y"] > 0]

    if player_x < 0:
        player_x = 0
    elif player_x > screen_x - player_width:
        player_x = screen_x - player_width

    if player_y < 0:
        player_y = 0
    elif player_y > screen_y - player_height:
        player_y = screen_y - player_height


    pygame.display.flip()
    pygame.display.update()

pygame.quit()