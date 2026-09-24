#!/usr/bin/env python3
"""
====================================================================
Soccer Bot Raspberry Pi Built-in Screen Navigation HUD
====================================================================
Renders real-time SLAM 2D Occupancy Grid map, robot position,
orientation needle, and spatial telemetry directly onto the
Raspberry Pi 480x320 LCD screen using Pygame.
====================================================================
"""

import base64
import json
import math
import socket
import struct
import sys
import threading
import time
import zlib
import pygame

# Configuration
LAPTOP_IP = "10.127.69.107"
LAPTOP_PORT = 8765
SCREEN_W = 480
SCREEN_H = 320
MAP_VIEW_W = 310
PANEL_W = 170

# Colors (Hex Theme)
BG_COLOR = (10, 14, 23)           # #0a0e17
PANEL_BG = (16, 23, 38)           # #101726
BORDER_COLOR = (35, 48, 74)       # #23304a
TEXT_CYAN = (0, 229, 255)         # #00e5ff
TEXT_WHITE = (240, 246, 252)      # #f0f6fc
TEXT_MUTED = (139, 148, 158)      # #8b949e
COLOR_FREE = (22, 32, 52)         # #162034
COLOR_WALL = (0, 240, 255)        # #00f0ff
COLOR_UNKNOWN = (8, 11, 18)       # #080b12
COLOR_ROBOT = (255, 68, 68)       # #ff4444
COLOR_ROBOT_ACC = (255, 215, 0)   # #ffd700
COLOR_PATH = (57, 255, 20)        # #39ff14
COLOR_CONNECTED = (46, 160, 67)   # Green
COLOR_DISCONNECTED = (248, 81, 73)# Red


class PiScreenHUD:
    def __init__(self, host=LAPTOP_IP, port=LAPTOP_PORT):
        self.host = host
        self.port = port
        self.running = True
        self.connected = False

        # Telemetry State
        self.lock = threading.Lock()
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.phone_yaw = 0.0
        self.path_points = []
        self.map_info = None
        self.map_surface = None
        self.map_w = 0
        self.map_h = 0
        self.map_res = 0.05
        self.map_ox = 0.0
        self.map_oy = 0.0
        self.zoom = 28.0  # Pixels per meter

        # Start network listener thread
        threading.Thread(target=self.network_loop, daemon=True).start()

    def network_loop(self):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4.0)
                s.connect((self.host, self.port))
                s.settimeout(None)
                self.connected = True

                while self.running:
                    # Read 4-byte big-endian length prefix
                    raw_len = self.recv_all(s, 4)
                    if not raw_len:
                        break
                    msg_len = struct.unpack('!I', raw_len)[0]
                    raw_data = self.recv_all(s, msg_len)
                    if not raw_data:
                        break

                    packet = json.loads(raw_data.decode('utf-8'))
                    self.process_packet(packet)
            except Exception:
                pass
            finally:
                self.connected = False
                try:
                    s.close()
                except Exception:
                    pass
                time.sleep(1.5)

    def recv_all(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def process_packet(self, packet):
        p_type = packet.get('type')
        if p_type == 'telemetry':
            pose = packet.get('pose', {})
            with self.lock:
                self.robot_x = float(pose.get('x', 0.0))
                self.robot_y = float(pose.get('y', 0.0))
                self.robot_yaw = float(pose.get('yaw_deg', 0.0))
                self.phone_yaw = float(packet.get('phone_yaw', 0.0))
                self.path_points = packet.get('path', [])
        elif p_type == 'map':
            try:
                w = packet['width']
                h = packet['height']
                res = packet['resolution']
                ox = packet['origin_x']
                oy = packet['origin_y']
                raw_b64 = packet['data']
                decompressed = zlib.decompress(base64.b64decode(raw_b64))

                # Create pygame surface for map
                surf = pygame.Surface((w, h))
                pixels = pygame.PixelArray(surf)

                # Unpack int8 cells
                for idx, val in enumerate(decompressed):
                    val = val if val < 128 else val - 256
                    x = idx % w
                    y = h - 1 - (idx // w)  # Flip Y for Cartesian coords
                    if val == 0:
                        pixels[x, y] = COLOR_FREE
                    elif val > 50:
                        pixels[x, y] = COLOR_WALL
                    else:
                        pixels[x, y] = COLOR_UNKNOWN
                del pixels

                with self.lock:
                    self.map_surface = surf
                    self.map_w = w
                    self.map_h = h
                    self.map_res = res
                    self.map_ox = ox
                    self.map_oy = oy
            except Exception:
                pass

    def run_gui(self):
        pygame.init()
        pygame.font.init()

        # Target full screen 480x320
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("⚽ SOCCER BOT NAV HUD")
        clock = pygame.time.Clock()

        # Fonts
        font_title = pygame.font.SysFont("DejaVu Sans,Ubuntu,Arial", 14, bold=True)
        font_main = pygame.font.SysFont("DejaVu Sans,Ubuntu,Arial", 12, bold=True)
        font_small = pygame.font.SysFont("DejaVu Sans,Ubuntu,Arial", 10)
        font_mono = pygame.font.SysFont("monospace,DejaVu Sans Mono", 11, bold=True)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.zoom = min(60.0, self.zoom + 4.0)
                    elif event.key == pygame.K_MINUS:
                        self.zoom = max(10.0, self.zoom - 4.0)

            # Snap state
            with self.lock:
                rx, ry, ryaw = self.robot_x, self.robot_y, self.robot_yaw
                pyaw = self.phone_yaw
                path = list(self.path_points)
                map_surf = self.map_surface
                map_w, map_h, map_res = self.map_w, self.map_h, self.map_res
                map_ox, map_oy = self.map_ox, self.map_oy

            # 1. Render Map Viewport (Left 310 x 320)
            map_rect = pygame.Rect(0, 0, MAP_VIEW_W, SCREEN_H)
            screen.fill(BG_COLOR, map_rect)

            center_x = MAP_VIEW_W // 2
            center_y = SCREEN_H // 2

            if map_surf:
                # Scale map according to zoom
                scale = (self.zoom * map_res)
                scaled_w = max(1, int(map_w * scale))
                scaled_h = max(1, int(map_h * scale))

                scaled_map = pygame.transform.scale(map_surf, (scaled_w, scaled_h))

                # World to Screen transform centered on Robot
                screen_map_x = center_x - int((rx - map_ox) * self.zoom)
                screen_map_y = center_y + int((ry - map_oy) * self.zoom) - scaled_h

                screen.blit(scaled_map, (screen_map_x, screen_map_y))

            # Draw Path Trajectory
            if len(path) > 1:
                screen_pts = []
                for pt in path:
                    sx = center_x + int((pt[0] - rx) * self.zoom)
                    sy = center_y - int((pt[1] - ry) * self.zoom)
                    if 0 <= sx < MAP_VIEW_W and 0 <= sy < SCREEN_H:
                        screen_pts.append((sx, sy))
                if len(screen_pts) > 1:
                    pygame.draw.lines(screen, COLOR_PATH, False, screen_pts, 2)

            # Draw Grid Crosshairs (Every 1 meter)
            meter_px = int(self.zoom)
            for gx in range(center_x % meter_px, MAP_VIEW_W, meter_px):
                pygame.draw.line(screen, (20, 28, 44), (gx, 0), (gx, SCREEN_H), 1)
            for gy in range(center_y % meter_px, SCREEN_H, meter_px):
                pygame.draw.line(screen, (20, 28, 44), (0, gy), (MAP_VIEW_W, gy), 1)

            # Draw Robot Marker at Center
            robot_rad = 12
            pygame.draw.circle(screen, COLOR_ROBOT_ACC, (center_x, center_y), robot_rad, 2)
            pygame.draw.circle(screen, COLOR_ROBOT, (center_x, center_y), 6)

            # Heading pointer arrow
            rad = math.radians(ryaw)
            arrow_len = 24
            tip_x = center_x + int(arrow_len * math.cos(rad))
            tip_y = center_y - int(arrow_len * math.sin(rad))
            pygame.draw.line(screen, COLOR_ROBOT_ACC, (center_x, center_y), (tip_x, tip_y), 3)

            # Mini Map Overlay Info (Top Left)
            map_dim_str = f"Map: {map_w * map_res:.1f}m x {map_h * map_res:.1f}m" if map_w else "Waiting for map..."
            lbl_dim = font_small.render(map_dim_str, True, TEXT_MUTED)
            screen.blit(lbl_dim, (8, 6))

            # 2. Render Telemetry Panel (Right 170 x 320)
            panel_rect = pygame.Rect(MAP_VIEW_W, 0, PANEL_W, SCREEN_H)
            screen.fill(PANEL_BG, panel_rect)
            pygame.draw.line(screen, BORDER_COLOR, (MAP_VIEW_W, 0), (MAP_VIEW_W, SCREEN_H), 2)

            # Title
            t1 = font_title.render("⚽ SOCCER BOT", True, TEXT_CYAN)
            t2 = font_small.render("SLAM NAVIGATION HUD", True, TEXT_MUTED)
            screen.blit(t1, (MAP_VIEW_W + 10, 8))
            screen.blit(t2, (MAP_VIEW_W + 10, 26))

            pygame.draw.line(screen, BORDER_COLOR, (MAP_VIEW_W + 6, 42), (SCREEN_W - 6, 42), 1)

            # Coordinates
            y_off = 50
            screen.blit(font_small.render("POSITION (MAP)", True, TEXT_MUTED), (MAP_VIEW_W + 10, y_off))
            y_off += 15
            screen.blit(font_mono.render(f"X: {rx:+.2f} m", True, TEXT_WHITE), (MAP_VIEW_W + 10, y_off))
            y_off += 18
            screen.blit(font_mono.render(f"Y: {ry:+.2f} m", True, TEXT_WHITE), (MAP_VIEW_W + 10, y_off))

            # Heading & Rotating Compass Needle
            y_off += 26
            screen.blit(font_small.render("HEADING", True, TEXT_MUTED), (MAP_VIEW_W + 10, y_off))
            y_off += 15
            screen.blit(font_mono.render(f"θ: {ryaw:+.1f}°", True, TEXT_CYAN), (MAP_VIEW_W + 10, y_off))

            # Draw Mini Compass Dial
            compass_cx = MAP_VIEW_W + 120
            compass_cy = y_off - 5
            compass_r = 22
            pygame.draw.circle(screen, BORDER_COLOR, (compass_cx, compass_cy), compass_r, 1)
            # Compass Needle
            c_rad = math.radians(ryaw)
            nx = compass_cx + int((compass_r - 4) * math.cos(c_rad))
            ny = compass_cy - int((compass_r - 4) * math.sin(c_rad))
            pygame.draw.line(screen, COLOR_ROBOT, (compass_cx, compass_cy), (nx, ny), 3)

            # Subsystem Status
            y_off += 30
            pygame.draw.line(screen, BORDER_COLOR, (MAP_VIEW_W + 6, y_off), (SCREEN_W - 6, y_off), 1)
            y_off += 8
            screen.blit(font_small.render("SYSTEM STATUS", True, TEXT_MUTED), (MAP_VIEW_W + 10, y_off))
            y_off += 16

            # SLAM status
            slam_col = COLOR_CONNECTED if map_surf else (255, 170, 0)
            slam_txt = "● SLAM ACTIVE" if map_surf else "● SCANNING..."
            screen.blit(font_main.render(slam_txt, True, slam_col), (MAP_VIEW_W + 10, y_off))
            y_off += 18

            # Gyro status
            gyro_txt = f"● GYRO: {pyaw:+.1f}°"
            screen.blit(font_main.render(gyro_txt, True, COLOR_CONNECTED), (MAP_VIEW_W + 10, y_off))
            y_off += 18

            # Motors status
            screen.blit(font_main.render("● MOTORS: READY", True, COLOR_CONNECTED), (MAP_VIEW_W + 10, y_off))

            # Bottom Status Bar (Connection & IP)
            y_off = SCREEN_H - 34
            pygame.draw.line(screen, BORDER_COLOR, (MAP_VIEW_W + 6, y_off), (SCREEN_W - 6, y_off), 1)
            y_off += 6
            if self.connected:
                conn_lbl = font_small.render("● LINK: ONLINE", True, COLOR_CONNECTED)
            else:
                conn_lbl = font_small.render("○ LINK: CONNECTING...", True, COLOR_DISCONNECTED)
            screen.blit(conn_lbl, (MAP_VIEW_W + 10, y_off))
            y_off += 13
            screen.blit(font_small.render(f"PI: 10.127.69.146", True, TEXT_MUTED), (MAP_VIEW_W + 10, y_off))

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else LAPTOP_IP
    hud = PiScreenHUD(host=host)
    hud.run_gui()
