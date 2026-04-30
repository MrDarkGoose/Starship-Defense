from pathlib import Path
import hashlib
import secrets
import base64
import random
import pygame
import json
import hmac
import math
import sys

# parameters

WIDTH = 1100
HEIGHT = 700
SIZE = 100
enemyWidth = 100
enemyHeight = 167
shipSpeed = 7
boostedSpeed = 11
bulletSpeed = 5
heartSpeed = 2
heartChance = 0.2
speedChance = 0.1
doubleChance = 0.1
baseEnemySpeed = 3
cornerEnemyChance = 0.35
cornerEnemyDrift = 2.6
heavyEnemyUnlockScore = 100
heavyEnemyChance = 0.22
heavyEnemyHp = 2
heavyEnemySpeedFactor = 0.6
baseSpawnDelay = 60
minSpawnDelay = 18
enemyStep = 35
spawnStep = 14
spawnDecrease = 1
shootDelay = 20
shotOffset = 18
maxHp = 5
invincibleDuration = 45
boostDuration = 360
FPS = 60
leaderboardLimit = 5
rootDir = Path(__file__).resolve().parent
assetDir = rootDir / "sprite"
saveFile = rootDir / "starship_high_score.json"
backupDir = Path.home() / "Documents" / "starshipdefance" / "save"
backupFile = backupDir / "starship_high_score.backup.json"
secretKey = b"starshipdefance-save-key-v1"
startX = 435
startY = 500

def makePayload(highScore, runs):
    normalizedRuns = []
    for index, item in enumerate(runs, start=1):
        if isinstance(item, dict):
            name = str(item.get("name", f"Player {index}")).strip() or f"Player {index}"
            score = int(item.get("score", 0))
        else:
            name = f"Player {index}"
            score = int(item)
        normalizedRuns.append({"name": name[:16], "score": score})
    return {"highScore": int(highScore), "runs": normalizedRuns}

def makeSignature(nonceText, cipherText):
    message = f"{nonceText}:{cipherText}".encode("utf-8")
    return hmac.new(secretKey, message, hashlib.sha256).hexdigest()

def makeKeyStream(length, nonceBytes):
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        blockInput = nonceBytes + counter.to_bytes(4, "big")
        stream.extend(hashlib.sha256(secretKey + blockInput).digest())
        counter += 1
    return bytes(stream[:length])

def xorBytes(dataBytes, keyBytes):
    return bytes(left ^ right for left, right in zip(dataBytes, keyBytes))

def encryptPayload(payload):
    plainText = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    nonceBytes = secrets.token_bytes(16)
    cipherBytes = xorBytes(plainText, makeKeyStream(len(plainText), nonceBytes))
    nonceText = base64.urlsafe_b64encode(nonceBytes).decode("ascii")
    cipherText = base64.urlsafe_b64encode(cipherBytes).decode("ascii")
    return {
        "version": 1,
        "nonce": nonceText,
        "ciphertext": cipherText,
        "signature": makeSignature(nonceText, cipherText),
    }

def decryptPayload(data):
    nonceText = str(data.get("nonce", ""))
    cipherText = str(data.get("ciphertext", ""))
    signature = str(data.get("signature", ""))

    if not hmac.compare_digest(signature, makeSignature(nonceText, cipherText)):
        raise ValueError("Invalid save signature")

    nonceBytes = base64.urlsafe_b64decode(nonceText.encode("ascii"))
    cipherBytes = base64.urlsafe_b64decode(cipherText.encode("ascii"))
    plainBytes = xorBytes(cipherBytes, makeKeyStream(len(cipherBytes), nonceBytes))
    payload = json.loads(plainBytes.decode("utf-8"))
    return makePayload(payload.get("highScore", 0), payload.get("runs", []))

def writeEncryptedSave(path, payload):
    encryptedData = encryptPayload(payload)
    tempFile = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempFile.open("w", encoding="utf-8") as file:
        json.dump(encryptedData, file, ensure_ascii=True, indent=2)
    tempFile.replace(path)

def loadEncryptedSave(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return decryptPayload(data)

def persistSave(payload):
    writeEncryptedSave(saveFile, payload)
    writeEncryptedSave(backupFile, payload)

def loadLegacySave(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return makePayload(data.get("highScore", data.get("high_score", 0)), data.get("runs", []))

def enemyAngle(dx, speed):
    return -math.degrees(math.atan2(dx, speed))

def makeEnemy(x, y, dx=0.0, hp=1, speedFactor=1.0):
    return [float(x), float(y), float(dx), enemyAngle(dx, max(speedFactor, 0.1)), int(hp), float(speedFactor)]

def createEnemy(speed, score):
    if random.random() < cornerEnemyChance:
        fromLeft = random.choice([True, False])
        dx = cornerEnemyDrift if fromLeft else -cornerEnemyDrift
        x = 0 if fromLeft else WIDTH - enemyWidth
        return makeEnemy(x, -enemyHeight, dx, 1, 1.0)

    hp = 1
    speedFactor = 1.0
    if score >= heavyEnemyUnlockScore and random.random() < heavyEnemyChance:
        hp = heavyEnemyHp
        speedFactor = heavyEnemySpeedFactor
    return makeEnemy(random.randint(0, WIDTH - enemyWidth), -enemyHeight, 0.0, hp, speedFactor)

def moveEnemy(enemy, speed):
    actualSpeed = speed * enemy[5]
    if enemy[2] != 0:
        enemy[0] += enemy[2] * enemy[5]
        enemy[3] = enemyAngle(enemy[2], actualSpeed)
    enemy[1] += actualSpeed

def getEnemyRect(enemy):
    return pygame.Rect(int(enemy[0]), int(enemy[1]), enemyWidth, enemyHeight)

def drawEnemy(screen, image, enemy):
    if enemy[2] != 0:
        manualTurn = -310 if enemy[2] > 0 else 310
        rotated = pygame.transform.rotate(image, manualTurn)
        center = (enemy[0] + enemyWidth / 2, enemy[1] + enemyHeight / 2)
        screen.blit(rotated, rotated.get_rect(center=center))
    else:
        screen.blit(image, (enemy[0], enemy[1]))

def loadAssets():
    ship = pygame.image.load(str(assetDir / "starship.png")).convert_alpha()
    ship = pygame.transform.scale(ship, (SIZE, SIZE))
    background = pygame.image.load(str(assetDir / "bg_space.png")).convert_alpha()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    laser = pygame.image.load(str(assetDir / "laser" / "bullet.png")).convert_alpha()
    laser = pygame.transform.scale(laser, (18, 46))
    enemy = pygame.image.load(str(assetDir / "comets.png")).convert_alpha()
    enemy = pygame.transform.scale(enemy, (enemyWidth, enemyHeight))
    heart = pygame.image.load(str(assetDir / "space_battery.png")).convert_alpha()
    heart = pygame.transform.scale(heart, (40, 40))

    return {
        "ship": ship,
        "background": background,
        "laser": laser,
        "enemy": enemy,
        "heart": heart,
    }

# highscore/results/leaderboard

def results():
    defaultData = {"highScore": 0, "runs": []}
    if saveFile.exists():
        try:
            return loadEncryptedSave(saveFile)
        except (ValueError, json.JSONDecodeError, OSError, TypeError):
            try:
                data = loadLegacySave(saveFile)
            except (ValueError, json.JSONDecodeError, OSError, TypeError):
                pass
            else:
                try:
                    persistSave(data)
                except OSError:
                    pass
                return data
    if backupFile.exists():
        try:
            data = loadEncryptedSave(backupFile)
        except (ValueError, json.JSONDecodeError, OSError, TypeError):
            return defaultData
        try:
            writeEncryptedSave(saveFile, data)
        except OSError:
            pass
        return data
    return defaultData

def loadHighScore():
    return results()["highScore"]

def loadLeaderboard(limit=leaderboardLimit):
    runs = results()["runs"]
    return sorted(runs, key=lambda item: item["score"], reverse=True)[:limit]

def saveResults(highScore, runs):
    payload = makePayload(highScore, runs)
    try:
        persistSave(payload)
    except OSError:
        pass

def saveHighScore(value):
    data = results()
    saveResults(value, data["runs"])

def recordRun(name, score):
    data = results()
    data["runs"].append({"name": (name.strip() or "Player")[:16], "score": int(score)})
    saveResults(max(int(score), data["highScore"]), data["runs"])

# states

def createState(highScore, playerName):
    return {
        "x": startX,
        "y": startY,
        "speed": shipSpeed,
        "baseSpeed": shipSpeed,
        "boostedSpeed": boostedSpeed,
        "bullets": [],
        "bulletSpeed": bulletSpeed,
        "enemies": [],
        "baseEnemySpeed": baseEnemySpeed,
        "enemySpeed": baseEnemySpeed,
        "spawnTimer": 0,
        "baseSpawnDelay": baseSpawnDelay,
        "spawnDelay": baseSpawnDelay,
        "minSpawnDelay": minSpawnDelay,
        "hearts": [],
        "speedBoosts": [],
        "doubleBoosts": [],
        "heartSpeed": heartSpeed,
        "heartChance": heartChance,
        "speedChance": speedChance,
        "doubleChance": doubleChance,
        "shootTimer": 0,
        "shootDelay": shootDelay,
        "shotOffset": shotOffset,
        "maxHp": maxHp,
        "hp": maxHp,
        "invincibleTimer": 0,
        "invincibleDuration": invincibleDuration,
        "score": 0,
        "highScore": highScore,
        "playerName": playerName,
        "gameState": "playing",
        "runRecorded": False,
        "speedTimer": 0,
        "doubleTimer": 0,
        "boostDuration": boostDuration,
    }

# controll

def resetRound(state):
    state["x"] = startX
    state["y"] = startY
    state["speed"] = state["baseSpeed"]
    state["bullets"].clear()
    state["enemies"].clear()
    state["hearts"].clear()
    state["speedBoosts"].clear()
    state["doubleBoosts"].clear()
    state["hp"] = state["maxHp"]
    state["score"] = 0
    state["shootTimer"] = 0
    state["spawnTimer"] = 0
    state["invincibleTimer"] = 0
    state["enemySpeed"] = state["baseEnemySpeed"]
    state["spawnDelay"] = state["baseSpawnDelay"]
    state["speedTimer"] = 0
    state["doubleTimer"] = 0
    state["gameState"] = "playing"
    state["runRecorded"] = False

def setPlayerName(state, playerName):
    state["playerName"] = playerName
    resetRound(state)

def finalizeRun(state):
    if state["runRecorded"]:
        return
    recordRun(state["playerName"], state["score"])
    state["runRecorded"] = True

# buffs

def spawnDrop(state, enemyX, enemyY):
    roll = random.random()
    if roll < state["heartChance"]:
        state["hearts"].append([enemyX, enemyY])
    elif roll < state["heartChance"] + state["speedChance"]:
        state["speedBoosts"].append([enemyX + 20, enemyY + 20])
    elif roll < state["heartChance"] + state["speedChance"] + state["doubleChance"]:
        state["doubleBoosts"].append([enemyX + 20, enemyY + 20])

def updateSpeed(state):
    if state["speedTimer"] > 0:
        state["speedTimer"] -= 1
        state["speed"] = state["boostedSpeed"]
    else:
        state["speed"] = state["baseSpeed"]

    if state["doubleTimer"] > 0:
        state["doubleTimer"] -= 1

def fireBullets(state):
    leftX = state["x"] + state["shotOffset"]
    rightX = state["x"] + SIZE - state["shotOffset"] - 10
    centerX = state["x"] + SIZE // 2 - 5

    if state["doubleTimer"] > 0:
        state["bullets"].append([leftX, state["y"] + 8])
        state["bullets"].append([rightX, state["y"] + 8])
    else:
        state["bullets"].append([centerX, state["y"]])

# logic games

def updateGame(state, keys):
    state["enemySpeed"] = state["baseEnemySpeed"] + state["score"] // enemyStep
    state["spawnDelay"] = max(
        state["minSpawnDelay"],
        state["baseSpawnDelay"] - (state["score"] // spawnStep) * spawnDecrease,
    )
    updateSpeed(state)

    if keys[pygame.K_LEFT]:
        state["x"] -= state["speed"]
    if keys[pygame.K_RIGHT]:
        state["x"] += state["speed"]
    if keys[pygame.K_UP]:
        state["y"] -= state["speed"]
    if keys[pygame.K_DOWN]:
        state["y"] += state["speed"]
    if state["x"] > WIDTH:
        state["x"] = -SIZE
    if state["x"] < -SIZE:
        state["x"] = WIDTH
    if state["y"] < 0:
        state["y"] = 0
    if state["y"] + SIZE > HEIGHT:
        state["y"] = HEIGHT - SIZE
    if state["invincibleTimer"] > 0:
        state["invincibleTimer"] -= 1
    state["shootTimer"] += 1
    if state["shootTimer"] >= state["shootDelay"]:
        fireBullets(state)
        state["shootTimer"] = 0
    for bullet in state["bullets"]:
        bullet[1] -= state["bulletSpeed"]
    state["bullets"] = [bullet for bullet in state["bullets"] if bullet[1] > -10]
    state["spawnTimer"] += 1
    if state["spawnTimer"] >= state["spawnDelay"]:
        state["enemies"].append(createEnemy(state["enemySpeed"], state["score"]))
        state["spawnTimer"] = 0
    
    shipRect = pygame.Rect(state["x"], state["y"], SIZE, SIZE)

    for enemy in state["enemies"][:]:
        moveEnemy(enemy, state["enemySpeed"])
        enemyRect = getEnemyRect(enemy)

        for bullet in state["bullets"][:]:
            bulletRect = pygame.Rect(bullet[0], bullet[1], 18, 46)
            if enemyRect.colliderect(bulletRect):
                state["bullets"].remove(bullet)
                enemy[4] -= 1
                if enemy[4] <= 0:
                    state["score"] += 1
                    if state["score"] > state["highScore"]:
                        state["highScore"] = state["score"]
                        saveHighScore(state["highScore"])
                    spawnDrop(state, enemy[0], enemy[1])
                    state["enemies"].remove(enemy)
                break

        if enemy in state["enemies"] and enemyRect.colliderect(shipRect):
            if state["invincibleTimer"] == 0:
                state["hp"] -= 1
                state["invincibleTimer"] = state["invincibleDuration"]
                if state["hp"] <= 0:
                    state["gameState"] = "lose"
                    finalizeRun(state)
            state["enemies"].remove(enemy)
        elif enemy in state["enemies"] and enemyRect.bottom >= HEIGHT:
            state["hp"] -= 1
            state["enemies"].remove(enemy)
            if state["hp"] <= 0:
                state["gameState"] = "lose"
                finalizeRun(state)

    for heart in state["hearts"][:]:
        heart[1] += state["heartSpeed"]
        heartRect = pygame.Rect(heart[0], heart[1], 40, 40)
        if heartRect.colliderect(shipRect):
            if state["hp"] < state["maxHp"]:
                state["hp"] += 1
            state["hearts"].remove(heart)
        elif heart[1] > HEIGHT:
            state["hearts"].remove(heart)

    for boost in state["speedBoosts"][:]:
        boost[1] += state["heartSpeed"]
        boostRect = pygame.Rect(boost[0], boost[1], 28, 28)
        if boostRect.colliderect(shipRect):
            state["speedTimer"] = state["boostDuration"]
            state["speedBoosts"].remove(boost)
        elif boost[1] > HEIGHT:
            state["speedBoosts"].remove(boost)

    for boost in state["doubleBoosts"][:]:
        boost[1] += state["heartSpeed"]
        boostRect = pygame.Rect(boost[0], boost[1], 28, 28)
        if boostRect.colliderect(shipRect):
            state["doubleTimer"] = state["boostDuration"]
            state["doubleBoosts"].remove(boost)
        elif boost[1] > HEIGHT:
            state["doubleBoosts"].remove(boost)

#draw

def drawPickup(screen, pickup, color, label):
    rect = pygame.Rect(pickup[0], pickup[1], 28, 28)
    pygame.draw.rect(screen, color, rect, border_radius=8)
    text = pygame.font.SysFont(None, 22).render(label, True, (15, 18, 25))
    screen.blit(text, text.get_rect(center=rect.center))

def drawCenteredLine(screen, text, y, color, font):
    line = font.render(text, True, color)
    screen.blit(line, line.get_rect(center=(WIDTH // 2, y)))

def drawEndPanel(screen):
    rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 85, 600, 170)
    pygame.draw.rect(screen, (12, 20, 34), rect, border_radius=16)
    pygame.draw.rect(screen, (90, 110, 140), rect, width=2, border_radius=16)

def drawGame(screen, assets, font, state, smallFont):
    screen.blit(assets["background"], (0, 0))

    if state["invincibleTimer"] == 0 or (state["invincibleTimer"] // 5) % 2 == 0:
        screen.blit(assets["ship"], (state["x"], state["y"]))

    for bullet in state["bullets"]:
        screen.blit(assets["laser"], (bullet[0], bullet[1]))
    for enemy in state["enemies"]:
        drawEnemy(screen, assets["enemy"], enemy)
    for heart in state["hearts"]:
        screen.blit(assets["heart"], (heart[0], heart[1]))
    for pickup in state["speedBoosts"]:
        drawPickup(screen, pickup, (80, 240, 180), "SPD")
    for pickup in state["doubleBoosts"]:
        drawPickup(screen, pickup, (255, 210, 90), "2X")

    scoreText = font.render(f"Destroyed: {state['score']}", True, (235, 240, 255))
    highScoreText = font.render(f"High score: {state['highScore']}", True, (255, 215, 0))
    difficultyText = font.render(f"Enemy speed: {state['enemySpeed']}", True, (180, 180, 255))
    hpText = font.render(f"HP: {state['hp']}", True, (255, 110, 110))
    playerText = font.render(f"Pilot: {state['playerName']}", True, (200, 255, 200))

    screen.blit(scoreText, (0, 40))
    screen.blit(highScoreText, (0, 70))
    screen.blit(difficultyText, (0, 100))
    screen.blit(hpText, hpText.get_rect(topright=(WIDTH - 10, 10)))
    screen.blit(playerText, playerText.get_rect(topright=(WIDTH - 10, 40)))

    if state["gameState"] == "lose":
        drawEndPanel(screen)
        drawCenteredLine(screen, "Game over!", HEIGHT // 2 - 38, (255, 110, 110), font)
        drawCenteredLine(screen, f"Destroyed: {state['score']}", HEIGHT // 2 + 4, (235, 240, 255), font)
        drawCenteredLine(screen, "SPACE - new plus run, ESC - back to menu", HEIGHT // 2 + 48, (220, 230, 255), smallFont)

    pygame.display.flip()

# plyer username

def collectName(screen, clock, font, titleFont):
    name = ""
    inputRect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 10, 440, 64)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN:
                    cleaned = name.strip()
                    return cleaned[:16] if cleaned else "Player"
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isprintable() and len(name) < 16:
                    name += event.unicode

        screen.fill((8, 12, 22))
        title = titleFont.render("Plus Run", True, (255, 255, 255))
        prompt = font.render("Enter pilot name and press ENTER", True, (220, 230, 255))
        helpText = font.render("Green = speed, yellow = double side cannons", True, (180, 210, 220))
        hint = font.render("ESC returns to the main menu", True, (180, 190, 210))
        typed = font.render(name or "_", True, (255, 255, 255))

        pygame.draw.rect(screen, (20, 30, 48), inputRect, border_radius=12)
        pygame.draw.rect(screen, (130, 190, 255), inputRect, width=3, border_radius=12)

        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 118)))
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 62)))
        screen.blit(helpText, helpText.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 88)))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 122)))
        screen.blit(typed, (inputRect.x + 18, inputRect.y + 18))

        pygame.display.flip()
        clock.tick(FPS)

# runs game

def runGame(screen=None, clock=None):
    pygame.init()
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    if clock is None:
        clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 36)
    smallFont = pygame.font.SysFont(None, 30)
    titleFont = pygame.font.SysFont(None, 64)

    assets = loadAssets()
    playerName = collectName(screen, clock, font, titleFont)
    if playerName is None:
        return

    state = createState(loadHighScore(), playerName)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        if state["gameState"] != "playing":
            if keys[pygame.K_SPACE]:
                nextName = collectName(screen, clock, font, titleFont)
                if nextName is None:
                    return
                setPlayerName(state, nextName)
            if keys[pygame.K_ESCAPE]:
                return

        if state["gameState"] == "playing":
            updateGame(state, keys)
        drawGame(screen, assets, font, state, smallFont)

if __name__ == "__main__":
    runGame()
