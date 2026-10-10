#!/usr/bin/env python3
"""Tanzanite Trail — full-colour Python 3 neon light-cycle arcade for ElbowOS.
Steer a glowing bike, leave a solid trail, collect orbs, avoid walls.
Python 3 + pygame. Autoplay 9:16 MP4 reel.
https://x.com/ElbowOS
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

# Record resolution 9:16
RW, RH, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/TANZANITE_TRAIL_ElbowOS.mp4")
TITLE, HANDLE = "TANZANITE TRAIL", "x.com/ElbowOS"

# Palette — deep indigo + tanzanite violet / cyan / gold
VOID = (6, 4, 18)
INK = (12, 8, 32)
CYAN = (40, 220, 255)
VIOLET = (160, 80, 255)
MAGENTA = (255, 50, 180)
GOLD = (255, 200, 60)
WHITE = (240, 245, 255)
LIME = (120, 255, 100)
ROSE = (255, 80, 110)

class Game:
    def __init__(self, record=False):
        pygame.init()
        self.record = record
        if record:
            self.screen = pygame.Surface((RW, RH))
            self.clock = pygame.time.Clock()
        else:
            self.screen = pygame.display.set_mode((540, 960))
            pygame.display.set_caption(TITLE)
            self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 36 if not record else 64, bold=True)
        self.small = pygame.font.SysFont("monospace", 24 if not record else 42, bold=True)
        self.reset()

    def reset(self):
        self.score = 0
        self.alive = True
        self.tick = 0
        # Grid for trail: cell size
        self.cs = 36 if self.record else 18
        self.gw = (RW if self.record else 540) // self.cs
        self.gh = (RH if self.record else 960) // self.cs
        # Start near bottom center, facing up
        self.cx = self.gw // 2
        self.cy = self.gh - 4
        self.dx, self.dy = 0, -1  # up
        self.trail = []  # list of (x,y) for order
        self.trail_set = set()
        self.trail.append((self.cx, self.cy))
        self.trail_set.add((self.cx, self.cy))
        self.orbs = []
        self.spawn_orbs(8)
        self.speed = 6  # frames per move
        self.move_cd = 0

    def spawn_orbs(self, n):
        for _ in range(n):
            while True:
                x = random.randint(2, self.gw - 3)
                y = random.randint(2, self.gh - 6)
                if (x, y) not in self.trail_set and (x, y) not in [(o[0], o[1]) for o in self.orbs]:
                    self.orbs.append([x, y, random.choice([CYAN, GOLD, LIME, MAGENTA])])
                    break

    def try_turn(self, ndx, ndy):
        # Prevent 180 reverse
        if (ndx, ndy) == (-self.dx, -self.dy):
            return
        self.dx, self.dy = ndx, ndy

    def ai_step(self):
        # Simple: look ahead, turn if wall or trail
        nx, ny = self.cx + self.dx, self.cy + self.dy
        blocked = (nx < 1 or nx >= self.gw - 1 or ny < 1 or ny >= self.gh - 1 or (nx, ny) in self.trail_set)
        if blocked or random.random() < 0.08:
            # Prefer turn left or right
            opts = [( -self.dy, self.dx), (self.dy, -self.dx)]
            random.shuffle(opts)
            for ox, oy in opts:
                tx, ty = self.cx + ox, self.cy + oy
                if 1 <= tx < self.gw - 1 and 1 <= ty < self.gh - 1 and (tx, ty) not in self.trail_set:
                    self.dx, self.dy = ox, oy
                    break

    def step(self):
        if not self.alive:
            return
        self.tick += 1
        self.move_cd += 1
        if self.move_cd >= max(3, self.speed):
            self.move_cd = 0
            nx, ny = self.cx + self.dx, self.cy + self.dy
            if nx < 1 or nx >= self.gw - 1 or ny < 1 or ny >= self.gh - 1 or (nx, ny) in self.trail_set:
                self.alive = False
                return
            self.cx, self.cy = nx, ny
            self.trail.append((self.cx, self.cy))
            self.trail_set.add((self.cx, self.cy))
            # Check orbs
            for o in self.orbs[:]:
                if o[0] == self.cx and o[1] == self.cy:
                    self.score += 10
                    self.orbs.remove(o)
                    self.spawn_orbs(1)
                    if self.speed > 2:
                        self.speed -= 0.1
            # Limit trail length so game continues
            if len(self.trail) > 100:
                old = self.trail.pop(0)
                self.trail_set.discard(old)

    def draw(self):
        sw = RW if self.record else 540
        sh = RH if self.record else 960
        self.screen.fill(VOID)
        # Subtle grid
        for i in range(0, sw, self.cs * 4):
            pygame.draw.line(self.screen, INK, (i, 0), (i, sh), 1)
        for j in range(0, sh, self.cs * 4):
            pygame.draw.line(self.screen, INK, (0, j), (sw, j), 1)
        # Trail
        for (tx, ty) in self.trail:
            px, py = tx * self.cs, ty * self.cs
            pygame.draw.rect(self.screen, VIOLET, (px + 2, py + 2, self.cs - 4, self.cs - 4))
            pygame.draw.rect(self.screen, CYAN, (px + 6, py + 6, self.cs - 12, self.cs - 12), 2)
        # Orbs
        for ox, oy, col in self.orbs:
            px = ox * self.cs + self.cs // 2
            py = oy * self.cs + self.cs // 2
            pygame.draw.circle(self.screen, col, (px, py), self.cs // 3)
            pygame.draw.circle(self.screen, WHITE, (px, py), self.cs // 5, 2)
        # Bike
        bx = self.cx * self.cs + self.cs // 2
        by = self.cy * self.cs + self.cs // 2
        pygame.draw.circle(self.screen, GOLD, (bx, by), self.cs // 2 - 2)
        pygame.draw.circle(self.screen, WHITE, (bx, by), self.cs // 3, 3)
        # Direction arrow
        ax = bx + self.dx * self.cs // 2
        ay = by + self.dy * self.cs // 2
        pygame.draw.line(self.screen, ROSE, (bx, by), (ax, ay), 4)
        # Overlay
        title_s = self.font.render(TITLE, True, GOLD)
        self.screen.blit(title_s, (20, 30 if self.record else 15))
        score_s = self.font.render(f"SCORE {self.score:04d}", True, CYAN)
        self.screen.blit(score_s, (20, 100 if self.record else 50))
        handle_s = self.small.render(HANDLE, True, MAGENTA)
        self.screen.blit(handle_s, (20, sh - 60 if self.record else sh - 40))
        if not self.alive:
            over = self.font.render("CRASH!", True, ROSE)
            self.screen.blit(over, (sw // 2 - 100, sh // 2))

    def record_video(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{RW}x{RH}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * SECS
        for f in range(frames):
            if self.alive:
                self.ai_step()
                self.step()
            self.draw()
            # RGB bytes
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
            if f % 30 == 0:
                print(f"frame {f}/{frames} score={self.score}")
        proc.stdin.close()
        proc.wait()
        print(f"Wrote {OUT}")

    def play_loop(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP or e.key == pygame.K_w:
                        self.try_turn(0, -1)
                    if e.key == pygame.K_DOWN or e.key == pygame.K_s:
                        self.try_turn(0, 1)
                    if e.key == pygame.K_LEFT or e.key == pygame.K_a:
                        self.try_turn(-1, 0)
                    if e.key == pygame.K_RIGHT or e.key == pygame.K_d:
                        self.try_turn(1, 0)
                    if e.key == pygame.K_r:
                        self.reset()
            if self.alive:
                self.step()
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()

if __name__ == "__main__":
    g = Game(record=RECORD)
    if RECORD:
        g.record_video()
    else:
        g.play_loop()
