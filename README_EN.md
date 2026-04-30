# Starship Defense

<p align="center">
  🌍 Languages: 
  <a href="README.md">Українська</a> |
  <a href="README_EN.md">English</a>
</p>

`Starship Defense` is an arcade game built with `pygame`, in which the player controls a starship, destroys comets, and protects Earth from a space threat.

## Mode Description

### Classic

`Classic` is a story mode.
According to the concept, the player is the last line of defense for Earth. Comets are flying toward the planet from space, and the pilot’s task is to repel them using the starship, preventing them from reaching the surface. Each destroyed comet brings the player closer to victory, while each missed attack once again puts Earth at risk.

In this mode, the game feels like a planetary defense mission:

- the ship patrols Earth’s orbit
- comets fall from above and diagonally
- the player shoots automatically and avoids collisions
- the goal is to withstand the attack and stop the wave of comets

### Plus

`Plus` is an endless mode.
Here there is no focus on completing a mission; instead, the main emphasis is on survival, pace, and score accumulation. Comets continue to come for longer and in greater density, and the player must survive as long as possible, set a record, and improve their result.

In this mode:

- the enemy flow continues without stopping
- difficulty gradually increases
- reaction, positioning, and survival are important
- the main result is the record number of destroyed comets

## What is in the project

- `starship_game.py` — basic version of the game
- `starship_game_plus.py` — extended version
- `sprite/` — sprites, background, and projectiles

## Launch

Install `pygame`:

```bash
pip install pygame-ce
```

## Compilation

To build the game into a single `.exe` file without a console window, use `PyInstaller`:

Install `PyInstaller`:
```bash
pip install pyinstaller
```
Compile the game:
```bash
pyinstaller --clean --noconfirm --onefile --windowed `
  --add-data "sprite\\bg_space.png;sprite" `
  --add-data "sprite\\comets.png;sprite" `
  --add-data "sprite\\space_battery.png;sprite" `
  --add-data "sprite\\starship.png;sprite" `
  --add-data "sprite\\laser\\bullet.png;sprite\\laser" `
  starship_game.py
```

After compilation, the ready file will be created in the `dist/` directory:

- `dist/starship_game.exe`

## Controls

- `Arrow keys` — move the ship
- `SPACE` — restart after defeat or victory
- `ESC` — go back or close the game

## Save system

For the test `plus` version, a separate high score file is used:

- main file: `test/test_starship_high_score.json`
- backup copy: `Documents/starshipdefance/save/starship_high_score.backup.json`

Якщо основний файл видалено, гра може відновити дані з резервної копії.