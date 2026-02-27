# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Görsel Efektler Modülü

Tüm prosedürel grafikler ve animasyon efektleri.
Ek kütüphane gerekmez — sadece pygame.draw + matematik.
"""

import math
import random
import pygame
from typing import List, Tuple, Optional
from config import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


# ═══════════════════════════════════════════════════════════
# 1. GRADIENT RENDERER
# ═══════════════════════════════════════════════════════════

class GradientRenderer:
    """Dikey gradient arka planlar — önbellekli."""

    THEMES = {
        'default':       ((30, 25, 35),  (20, 18, 28)),
        'military':      ((35, 25, 30),  (15, 12, 25)),
        'economy':       ((25, 35, 30),  (15, 20, 18)),
        'trade':         ((35, 30, 20),  (20, 15, 12)),
        'battle':        ((45, 20, 20),  (15, 10, 10)),
        'naval':         ((20, 25, 40),  (10, 15, 30)),
        'diplomacy':     ((35, 30, 40),  (20, 18, 28)),
        'religion':      ((25, 30, 35),  (15, 20, 25)),
        'artillery':     ((30, 28, 25),  (18, 15, 12)),
        'construction':  ((30, 30, 25),  (18, 18, 12)),
        'espionage':     ((20, 18, 28),  (10, 8, 15)),
        'menu':          ((25, 20, 35),  (12, 10, 20)),
        'map':           ((25, 30, 25),  (15, 18, 15)),
        'victory':       ((40, 35, 15),  (20, 18, 8)),
        'defeat':        ((35, 15, 15),  (18, 8, 8)),
    }

    _cache = {}

    @classmethod
    def get_gradient(cls, theme='default',
                     width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        key = (theme, width, height)
        if key in cls._cache:
            return cls._cache[key]
        colors = cls.THEMES.get(theme, cls.THEMES['default'])
        surface = cls._make(width, height, colors[0], colors[1])
        cls._cache[key] = surface
        return surface

    @staticmethod
    def _make(w, h, top, bot):
        s = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (w, y))
        return s


# ═══════════════════════════════════════════════════════════
# 2. PARTICLE SYSTEM
# ═══════════════════════════════════════════════════════════

class Particle:
    __slots__ = ['x','y','vx','vy','size','color','alpha','life','max_life','shape']
    def __init__(self, x, y, vx, vy, size, color, life, shape='circle'):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.size = size
        self.color = color
        self.alpha = 255
        self.life = self.max_life = life
        self.shape = shape


class ParticleSystem:
    """Mevsimsel parçacık efektleri."""

    def __init__(self, max_particles=60):
        self.particles: List[Particle] = []
        self.max_particles = max_particles
        self.active = True
        self._time = 0.0
        self._season = 'spring'

    def set_season(self, season):
        self.particles.clear()
        self._season = season

    def update(self, dt):
        if not self.active:
            return
        self._time += dt
        if len(self.particles) < self.max_particles:
            self._spawn()
        alive = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            if p.shape == 'leaf':
                p.vx = math.sin(self._time * 2 + p.y * 0.01) * 20
            if p.life > 0:
                p.alpha = int(255 * min(1.0, (p.life / p.max_life) * 2))
                alive.append(p)
        self.particles = alive

    def _spawn(self):
        s = self._season
        if s == 'spring':
            p = Particle(random.randint(0, SCREEN_WIDTH), random.randint(-20, -5),
                         random.uniform(-15, 15), random.uniform(20, 50),
                         random.randint(2, 4), (255, 200, 220),
                         random.uniform(8, 15), 'leaf')
        elif s == 'summer':
            p = Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT),
                         random.uniform(-5, 5), random.uniform(-3, 3),
                         random.randint(1, 2), (200, 190, 150),
                         random.uniform(3, 7), 'circle')
        elif s == 'autumn':
            p = Particle(random.randint(0, SCREEN_WIDTH), random.randint(-20, -5),
                         random.uniform(-10, 10), random.uniform(25, 60),
                         random.randint(3, 5),
                         random.choice([(200,120,40),(180,80,30),(160,60,20),(220,160,50)]),
                         random.uniform(6, 12), 'leaf')
        elif s == 'winter':
            p = Particle(random.randint(0, SCREEN_WIDTH), random.randint(-20, -5),
                         random.uniform(-10, 10), random.uniform(15, 40),
                         random.randint(1, 3), (230, 235, 245),
                         random.uniform(10, 20), 'circle')
        else:
            return
        self.particles.append(p)

    def draw(self, surface):
        if not self.active:
            return
        for p in self.particles:
            if p.alpha <= 0:
                continue
            if p.shape == 'circle':
                if p.alpha >= 200:
                    pygame.draw.circle(surface, p.color, (int(p.x), int(p.y)), p.size)
                else:
                    s = pygame.Surface((p.size*2, p.size*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*p.color, p.alpha), (p.size, p.size), p.size)
                    surface.blit(s, (int(p.x)-p.size, int(p.y)-p.size))
            elif p.shape == 'leaf':
                angle = self._time * 1.5 + p.x * 0.1
                cs, sn = math.cos(angle)*p.size, math.sin(angle)*p.size
                cx, cy = int(p.x), int(p.y)
                pts = [(cx+cs, cy+sn), (cx-sn*0.5, cy+cs*0.5), (cx-cs*0.7, cy-sn*0.7)]
                if p.alpha >= 200:
                    pygame.draw.polygon(surface, p.color, pts)
                else:
                    s2 = pygame.Surface((p.size*4, p.size*4), pygame.SRCALPHA)
                    off = [(x-cx+p.size*2, y-cy+p.size*2) for x, y in pts]
                    pygame.draw.polygon(s2, (*p.color, p.alpha), off)
                    surface.blit(s2, (cx-p.size*2, cy-p.size*2))


class SparkleSystem:
    """Ana menü için parlayıp sönen altın kıvılcımlar."""

    def __init__(self, count=25):
        self.sparkles = []
        self._time = 0.0
        for _ in range(count):
            self.sparkles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.5, 2.0),
                'size': random.randint(1, 3),
                'color': random.choice([(218,165,32),(255,200,80),(200,150,50)]),
            })

    def update(self, dt):
        self._time += dt
        for s in self.sparkles:
            s['x'] += math.sin(self._time * s['speed'] + s['phase']) * 0.3
            s['y'] += math.cos(self._time * s['speed'] * 0.7 + s['phase']) * 0.2
            if s['x'] < 0: s['x'] = SCREEN_WIDTH
            if s['x'] > SCREEN_WIDTH: s['x'] = 0
            if s['y'] < 0: s['y'] = SCREEN_HEIGHT
            if s['y'] > SCREEN_HEIGHT: s['y'] = 0

    def draw(self, surface):
        for s in self.sparkles:
            br = (math.sin(self._time * s['speed'] * 2 + s['phase']) + 1) * 0.5
            alpha = int(40 + br * 180)
            if alpha > 30:
                gs = s['size'] + int(br * 2)
                gsurf = pygame.Surface((gs*4, gs*4), pygame.SRCALPHA)
                pygame.draw.circle(gsurf, (*s['color'], alpha//3), (gs*2, gs*2), gs*2)
                pygame.draw.circle(gsurf, (*s['color'], alpha), (gs*2, gs*2), gs)
                surface.blit(gsurf, (int(s['x'])-gs*2, int(s['y'])-gs*2))


# ═══════════════════════════════════════════════════════════
# 3. OTTOMAN PATTERNS
# ═══════════════════════════════════════════════════════════

class OttomanPatterns:
    """Osmanlı geometrik desenleri."""

    @classmethod
    def draw_ornamental_divider(cls, surface, y, width=400,
                                 color=None, center_x=None):
        if color is None: color = COLORS['gold']
        if center_x is None: center_x = SCREEN_WIDTH // 2
        half = width // 2
        left, right = center_x - half, center_x + half
        pygame.draw.line(surface, color, (left+30, y), (right-30, y), 2)
        ds = 6
        diamond = [(center_x, y-ds), (center_x+ds, y), (center_x, y+ds), (center_x-ds, y)]
        pygame.draw.polygon(surface, color, diamond)
        for o in [-1, 1]:
            tx = center_x + o * 40
            pygame.draw.polygon(surface, color, [(tx, y-3), (tx+o*5, y), (tx, y+3)])
        pygame.draw.circle(surface, color, (left+20, y), 3)
        pygame.draw.circle(surface, color, (right-20, y), 3)

    @classmethod
    def draw_corner_ornament(cls, surface, x, y, size=20, corner='tl', color=None):
        if color is None: color = COLORS['gold']
        dx = 1 if corner in ('tl','bl') else -1
        dy = 1 if corner in ('tl','tr') else -1
        pygame.draw.line(surface, color, (x, y), (x+dx*size, y), 2)
        pygame.draw.line(surface, color, (x, y), (x, y+dy*size), 2)
        pygame.draw.circle(surface, color, (x, y), 3)
        inner = size // 3
        pygame.draw.line(surface, color, (x+dx*5, y+dy*5), (x+dx*(5+inner), y+dy*5), 1)
        pygame.draw.line(surface, color, (x+dx*5, y+dy*5), (x+dx*5, y+dy*(5+inner)), 1)

    @classmethod
    def draw_panel_ornaments(cls, surface, rect, color=None):
        if color is None: color = COLORS.get('gold', (218,165,32))
        corners = {
            'tl': (rect.left+4, rect.top+4), 'tr': (rect.right-4, rect.top+4),
            'bl': (rect.left+4, rect.bottom-4), 'br': (rect.right-4, rect.bottom-4),
        }
        for cn, (cx, cy) in corners.items():
            cls.draw_corner_ornament(surface, cx, cy, size=15, corner=cn, color=color)

    @classmethod
    def draw_eight_point_star(cls, surface, cx, cy, size, color=None):
        if color is None: color = COLORS['gold']
        pa, pb = [], []
        for i in range(4):
            a = math.radians(i*90+45)
            b = math.radians(i*90)
            pa.append((cx+math.cos(a)*size, cy+math.sin(a)*size))
            pb.append((cx+math.cos(b)*size, cy+math.sin(b)*size))
        pygame.draw.polygon(surface, color, pa, 2)
        pygame.draw.polygon(surface, color, pb, 2)
        pygame.draw.circle(surface, color, (cx, cy), size//3, 1)

    @classmethod
    def draw_title_frame(cls, surface, text_rect, color=None):
        if color is None: color = COLORS['gold']
        frame = text_rect.inflate(40, 16)
        pygame.draw.line(surface, color, (frame.left, frame.top), (frame.right, frame.top), 1)
        pygame.draw.line(surface, color, (frame.left, frame.bottom), (frame.right, frame.bottom), 1)
        for (cx, cy) in [(frame.left, frame.top), (frame.right, frame.top),
                          (frame.left, frame.bottom), (frame.right, frame.bottom)]:
            pygame.draw.circle(surface, color, (cx, cy), 3)
        cls.draw_eight_point_star(surface, frame.left-15, frame.centery, 6, color)
        cls.draw_eight_point_star(surface, frame.right+15, frame.centery, 6, color)


# ═══════════════════════════════════════════════════════════
# 4. RESOURCE BAR
# ═══════════════════════════════════════════════════════════

class ResourceBar:
    @staticmethod
    def draw(surface, x, y, width, height, value, max_value,
             color=None, show_glow=True, label=None):
        ratio = min(1.0, max(0.0, value / max_value)) if max_value > 0 else 0
        if color is None:
            if ratio > 0.6:   color = (34, 139, 34)
            elif ratio > 0.3: color = (218, 165, 32)
            else:             color = (178, 34, 34)
        bg = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (30, 28, 35), bg, border_radius=4)
        pygame.draw.rect(surface, (60, 55, 70), bg, width=1, border_radius=4)
        fw = int(width * ratio)
        if fw > 0:
            fr = pygame.Rect(x, y, fw, height)
            pygame.draw.rect(surface, color, fr, border_radius=4)
            if show_glow and fw > 4:
                gr = pygame.Rect(x+1, y+1, fw-2, height//2)
                gs = pygame.Surface((gr.width, gr.height), pygame.SRCALPHA)
                pygame.draw.rect(gs, (255,255,255,40), gs.get_rect(), border_radius=3)
                surface.blit(gs, gr.topleft)
        if label:
            from config import get_font, FONTS
            font = get_font(FONTS['small'])
            t = font.render(label, True, (255,255,255))
            surface.blit(t, t.get_rect(midleft=(x+5, y+height//2)))


# ═══════════════════════════════════════════════════════════
# 5. SCREEN SHAKE
# ═══════════════════════════════════════════════════════════

class ScreenShake:
    def __init__(self):
        self.offset_x = self.offset_y = 0
        self._intensity = self._duration = self._time = 0

    def trigger(self, intensity=8.0, duration=0.3):
        self._intensity = intensity
        self._duration = duration
        self._time = 0

    def update(self, dt):
        if self._duration <= 0:
            self.offset_x = self.offset_y = 0
            return
        self._time += dt
        if self._time >= self._duration:
            self._duration = 0
            self.offset_x = self.offset_y = 0
            return
        decay = 1.0 - (self._time / self._duration)
        ci = self._intensity * decay
        self.offset_x = int(random.uniform(-ci, ci))
        self.offset_y = int(random.uniform(-ci, ci))

    @property
    def is_active(self): return self._duration > 0


# ═══════════════════════════════════════════════════════════
# 6. FLASH EFFECT
# ═══════════════════════════════════════════════════════════

class FlashEffect:
    def __init__(self):
        self._alpha = 0
        self._color = (255, 255, 255)
        self._duration = self._time = 0

    def trigger(self, color=(255, 220, 150), duration=0.15):
        self._color = color
        self._duration = duration
        self._time = 0
        self._alpha = 200

    def update(self, dt):
        if self._duration <= 0: return
        self._time += dt
        if self._time >= self._duration:
            self._duration = 0; self._alpha = 0; return
        self._alpha = int(200 * (1.0 - self._time / self._duration))

    def draw(self, surface):
        if self._alpha > 0:
            fs = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fs.fill((*self._color, self._alpha))
            surface.blit(fs, (0, 0))

    @property
    def is_active(self): return self._duration > 0


# ═══════════════════════════════════════════════════════════
# 7. PULSE TEXT
# ═══════════════════════════════════════════════════════════

class PulseText:
    def __init__(self):
        self._time = 0.0

    def update(self, dt):
        self._time += dt

    def get_color(self, base_color, speed=1.0):
        wave = (math.sin(self._time * speed) + 1) * 0.5
        f = 0.78 + wave * 0.22
        return (min(255, int(base_color[0]*f)), min(255, int(base_color[1]*f)),
                min(255, int(base_color[2]*f)))
