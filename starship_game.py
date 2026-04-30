from starship_game_plus import loadLeaderboard, runGame as runPlusGame
from pathlib import Path
import random
import pygame
import math
import sys

pygame.init()

# parameters

WIDTH = 1100
HEIGHT = 700
SIZE = 100
enemyWidth = 100
enemyHeight = 167
cornerEnemyChance = 0.35
cornerEnemyDrift = 2.6
assetDir = Path(__file__).resolve().parent / "sprite"
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starship Defense")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
titleFont = pygame.font.SysFont(None, 72)
menuFont = pygame.font.SysFont(None, 44)
smallFont = pygame.font.SysFont(None, 30)
sprite = pygame.image.load(str(assetDir / "starship.png")).convert_alpha()
sprite = pygame.transform.scale(sprite, (SIZE, SIZE))
bg = pygame.image.load(str(assetDir / "bg_space.png")).convert_alpha()
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
laser = pygame.image.load(str(assetDir / "laser" / "bullet.png")).convert_alpha()
laser = pygame.transform.scale(laser, (18, 46))
enemyImg = pygame.image.load(str(assetDir / "comets.png")).convert_alpha()
enemyImg = pygame.transform.scale(enemyImg, (enemyWidth, enemyHeight))
heartImg = pygame.image.load(str(assetDir / "space_battery.png")).convert_alpha()
heartImg = pygame.transform.scale(heartImg, (40, 40))

def enemyAngle(dx, speed):
    return -math.degrees(math.atan2(dx, speed))

# enemy

def createEnemy(speed):
    if random.random() < cornerEnemyChance:
        fromLeft = random.choice([True, False])
        dx = cornerEnemyDrift if fromLeft else -cornerEnemyDrift
        x = 0 if fromLeft else WIDTH - enemyWidth
        return [float(x), float(-enemyHeight), dx, enemyAngle(dx, speed)]
    return [random.randint(0, WIDTH - enemyWidth), -enemyHeight]

def moveEnemy(enemy, speed):
    if len(enemy) > 2:
        enemy[0] += enemy[2]
        enemy[3] = enemyAngle(enemy[2], speed)
    enemy[1] += speed

def getEnemyRect(enemy):
    return pygame.Rect(int(enemy[0]), int(enemy[1]), enemyWidth, enemyHeight)

# draw

def drawEnemy(image, enemy):
    if len(enemy) > 2:
        manualTurn = 90 if enemy[2] > 0 else 270
        rotated = pygame.transform.rotate(image, enemy[3] + manualTurn)
        center = (enemy[0] + enemyWidth / 2, enemy[1] + enemyHeight / 2)
        screen.blit(rotated, rotated.get_rect(center=center))
    else:
        screen.blit(image, (enemy[0], enemy[1]))

def drawButton(rect, label, active):
    fill = (32, 60, 100) if active else (18, 28, 46)
    border = (130, 190, 255) if active else (90, 110, 140)
    pygame.draw.rect(screen, fill, rect, border_radius=14)
    pygame.draw.rect(screen, border, rect, width=3, border_radius=14)
    text = menuFont.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))

def drawCenteredLine(text, y, color=(255, 255, 255), usedFont=None):
    usedFont = usedFont or font
    line = usedFont.render(text, True, color)
    screen.blit(line, line.get_rect(center=(WIDTH // 2, y)))

def drawEndPanel():
    rect = pygame.Rect(WIDTH // 2 - 275, HEIGHT // 2 - 80, 550, 160)
    pygame.draw.rect(screen, (12, 20, 34), rect, border_radius=16)
    pygame.draw.rect(screen, (90, 110, 140), rect, width=2, border_radius=16)

#menu

def showModeMenu():
    classicRect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 10, 200, 80)
    plusRect = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 - 10, 200, 80)

    while True:
        mousePos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "classic"
                if event.key == pygame.K_2:
                    return "plus"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if classicRect.collidepoint(event.pos):
                    return "classic"
                if plusRect.collidepoint(event.pos):
                    return "plus"

        screen.blit(bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        screen.blit(overlay, (0, 0))
        title = titleFont.render("Starship Defense", True, (255, 255, 255))
        hint = font.render("Press 1 / 2 or click a button", True, (220, 230, 255))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55)))
        drawButton(classicRect, "1. Classic", classicRect.collidepoint(mousePos))
        drawButton(plusRect, "2. Plus game", plusRect.collidepoint(mousePos))

        leaderboard = loadLeaderboard()
        boardRect = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 + 110, 500, 220)
        pygame.draw.rect(screen, (12, 20, 34), boardRect, border_radius=16)
        pygame.draw.rect(screen, (90, 110, 140), boardRect, width=2, border_radius=16)
        boardTitle = menuFont.render("Plus Top 5", True, (255, 215, 0))
        screen.blit(boardTitle, (boardRect.x + 110, boardRect.y + 16))

        if leaderboard:
            for index, item in enumerate(leaderboard, start=1):
                line = smallFont.render(
                    f"{index}. {item['name']} - {item['score']} comets",
                    True,
                    (235, 240, 255),
                )
                screen.blit(line, (boardRect.x + 26, boardRect.y + 60 + (index - 1) * 28))
        else:
            emptyText = smallFont.render("No plus runs yet", True, (210, 220, 240))
            screen.blit(emptyText, (boardRect.x + 130, boardRect.y + 100))
        pygame.display.flip()
        clock.tick(60)

#classic game

def runClassicGame():
    x, y = 435, 500
    speed = 7
    bullets = []
    enemies = []
    hearts = []
    bulletSpeed = 5
    enemySpeed = 3
    spawnTimer = 0
    spawnDelay = 60
    heartSpeed = 2
    heartChance = 0.2
    shootTimer = 0
    shootDelay = 20
    maxHp = 5
    hp = maxHp
    invincibleTimer = 0
    invincibleDuration = 45
    score = 0
    gameState = "playing"

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        # status
        if gameState != "playing":
            if keys[pygame.K_SPACE]:
                x, y = 435, 500
                bullets.clear()
                enemies.clear()
                hearts.clear()
                hp = maxHp
                invincibleTimer = 0
                score = 0
                shootTimer = 0
                spawnTimer = 0
                gameState = "playing"
            if keys[pygame.K_ESCAPE]:
                return
        # controlls
        if gameState == "playing":
            if keys[pygame.K_LEFT]:
                x -= speed
            if keys[pygame.K_RIGHT]:
                x += speed
            if keys[pygame.K_UP]:
                y -= speed
            if keys[pygame.K_DOWN]:
                y += speed

            if x > WIDTH:
                x = -SIZE
            if x < -SIZE:
                x = WIDTH
            if y < 0:
                y = 0
            if y + SIZE > HEIGHT:
                y = HEIGHT - SIZE
            # gameplay
            if invincibleTimer > 0:
                invincibleTimer -= 1

            shootTimer += 1
            if shootTimer >= shootDelay:
                bullets.append([x + SIZE // 2 - 5, y])
                shootTimer = 0

            for bullet in bullets:
                bullet[1] -= bulletSpeed
            bullets = [bullet for bullet in bullets if bullet[1] > -10]

            spawnTimer += 1
            if spawnTimer >= spawnDelay:
                enemies.append(createEnemy(enemySpeed))
                spawnTimer = 0

            shipRect = pygame.Rect(x, y, SIZE, SIZE)

            for enemy in enemies[:]:
                moveEnemy(enemy, enemySpeed)
                enemyRect = getEnemyRect(enemy)

                for bullet in bullets[:]:
                    bulletRect = pygame.Rect(bullet[0], bullet[1], 18, 46)
                    if enemyRect.colliderect(bulletRect):
                        bullets.remove(bullet)
                        score += 1
                        if score >= 100:
                            gameState = "win"
                        if random.random() < heartChance:
                            hearts.append([enemy[0], enemy[1]])
                        enemies.remove(enemy)
                        break

                if enemy in enemies and enemyRect.colliderect(shipRect):
                    if invincibleTimer == 0:
                        hp -= 1
                        invincibleTimer = invincibleDuration
                        if hp <= 0:
                            gameState = "lose"
                    enemies.remove(enemy)
                elif enemy in enemies and enemyRect.bottom >= HEIGHT:
                    hp -= 1
                    enemies.remove(enemy)
                    if hp <= 0:
                        gameState = "lose"

            for heart in hearts[:]:
                heart[1] += heartSpeed
                heartRect = pygame.Rect(heart[0], heart[1], 40, 40)
                if heartRect.colliderect(shipRect):
                    if hp < maxHp:
                        hp += 1
                    hearts.remove(heart)
                elif heart[1] > HEIGHT:
                    hearts.remove(heart)

        screen.blit(bg, (0, 0))
        if invincibleTimer == 0 or (invincibleTimer // 5) % 2 == 0:
            screen.blit(sprite, (x, y))

        for bullet in bullets:
            screen.blit(laser, (bullet[0], bullet[1]))
        for enemy in enemies:
            drawEnemy(enemyImg, enemy)
        for heart in hearts:
            screen.blit(heartImg, (heart[0], heart[1]))

        scoreText = font.render(f"Destroyed: {score}", True, (235, 240, 255))
        hpText = font.render(f"HP: {hp}", True, (255, 110, 110))
        screen.blit(scoreText, (0, 40))
        screen.blit(hpText, hpText.get_rect(topright=(WIDTH - 10, 10)))

        if gameState == "win":
            drawEndPanel()
            drawCenteredLine("You win!", HEIGHT // 2 - 28, (110, 255, 160), menuFont)
            drawCenteredLine("SPACE - restart, ESC - menu", HEIGHT // 2 + 28, (220, 230, 255))
        elif gameState == "lose":
            drawEndPanel()
            drawCenteredLine("Game over!", HEIGHT // 2 - 28, (255, 110, 110), menuFont)
            drawCenteredLine("SPACE - restart, ESC - menu", HEIGHT // 2 + 28, (220, 230, 255))
        pygame.display.flip()

#runs game

def main():
    while True:
        selectedMode = showModeMenu()
        if selectedMode == "plus":
            runPlusGame(screen, clock)
        else:
            runClassicGame()

if __name__ == "__main__":
    main()
