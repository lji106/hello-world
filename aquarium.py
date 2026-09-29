#!/usr/bin/env python3
"""A tiny ASCII aquarium for your terminal. Press Ctrl+C to leave the fish alone."""

import random
import shutil
import sys
import time

FPS = 10

RESET = "\033[0m"
COLORS = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m"]
WATER = "\033[34m"
SAND = "\033[33m"
WEED = "\033[32m"
BUBBLE = "\033[96m"

# Each fish has a right-facing and a left-facing sprite.
FISH = [
    ("><>", "<><"),
    ("><(('>", "<'))><"),
    (">-=>", "<=-<"),
    ("}<>", "<>{"),
    ("><((((º>", "<º))))><"),
    ("><_>", "<_><"),
]

SHARK = ("__/\\____/\\______>", "<______/\\____/\\__")


class Fish:
    def __init__(self, width, height, sprites=None, color=None):
        self.sprites = sprites or random.choice(FISH)
        self.color = color or random.choice(COLORS)
        self.speed = random.uniform(0.3, 1.2)
        self.reset(width, height)

    def reset(self, width, height):
        self.right = random.random() < 0.5
        self.sprite = self.sprites[0] if self.right else self.sprites[1]
        self.x = -len(self.sprite) if self.right else width
        self.y = random.randint(2, max(2, height - 4))

    def update(self, width, height):
        self.x += self.speed if self.right else -self.speed
        if self.x > width + 1 or self.x < -len(self.sprite) - 1:
            self.reset(width, height)
        # A little vertical wander keeps things lively.
        if random.random() < 0.03:
            self.y = min(max(2, self.y + random.choice((-1, 1))), height - 4)


class Bubble:
    def __init__(self, x, y):
        self.x = x
        self.y = float(y)

    def update(self):
        self.y -= 0.5
        if random.random() < 0.2:
            self.x += random.choice((-1, 1))

    @property
    def char(self):
        return "O" if self.y > 8 else "o" if self.y > 4 else "."


def draw(grid, x, y, text, color):
    x = int(round(x))
    y = int(round(y))
    if not 0 <= y < len(grid):
        return
    row = grid[y]
    for i, ch in enumerate(text):
        if 0 <= x + i < len(row):
            row[x + i] = color + ch + RESET


def main():
    width, height = shutil.get_terminal_size((80, 24))
    height -= 1  # leave room so the terminal doesn't scroll

    fish = [Fish(width, height) for _ in range(max(4, width // 12))]
    bubbles = []
    weeds = [random.randint(0, width - 1) for _ in range(max(3, width // 10))]
    weed_heights = [random.randint(2, max(2, height // 3)) for _ in weeds]
    shark = None
    frame = 0

    sys.stdout.write("\033[?25l\033[2J")  # hide cursor, clear screen
    try:
        while True:
            new_w, new_h = shutil.get_terminal_size((80, 24))
            if (new_w, new_h - 1) != (width, height):
                width, height = new_w, new_h - 1
                sys.stdout.write("\033[2J")

            grid = [[" "] * width for _ in range(height)]

            # Surface waves.
            waves = "~^" if frame % 10 < 5 else "^~"
            draw(grid, 0, 0, (waves * width)[:width], WATER)

            # Sandy floor.
            draw(grid, 0, height - 1, ("_.,-" * width)[:width], SAND)

            # Swaying seaweed.
            for wx, wh in zip(weeds, weed_heights):
                if wx >= width:
                    continue
                for i in range(wh):
                    sway = "(" if (i + frame // 5) % 2 else ")"
                    draw(grid, wx, height - 2 - i, sway, WEED)

            # Bubbles drift up from the seaweed and fish.
            if random.random() < 0.15 and weeds:
                bubbles.append(Bubble(random.choice(weeds), height - 2))
            for b in bubbles:
                b.update()
            bubbles = [b for b in bubbles if b.y > 1]
            for b in bubbles:
                draw(grid, b.x, b.y, b.char, BUBBLE)

            for f in fish:
                f.update(width, height)
                draw(grid, f.x, f.y, f.sprite, f.color)
                if random.random() < 0.01:
                    bubbles.append(Bubble(int(f.x), f.y - 1))

            # Very occasionally, a shark passes through.
            if shark is None and random.random() < 0.002:
                shark = Fish(width, height, SHARK, "\033[97m")
                shark.speed = 1.5
            if shark:
                shark.x += shark.speed if shark.right else -shark.speed
                if shark.x > width or shark.x < -len(shark.sprite):
                    shark = None
                else:
                    draw(grid, shark.x, shark.y, shark.sprite, shark.color)

            out = "\033[H" + "\n".join("".join(row) for row in grid)
            sys.stdout.write(out)
            sys.stdout.flush()

            frame += 1
            time.sleep(1 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\033[?25h\033[2J\033[H")
        print("The fish say bye. ><>")


if __name__ == "__main__":
    main()
