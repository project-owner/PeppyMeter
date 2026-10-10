# Copyright 2026 PeppyMeter
#
# This file is part of PeppyMeter and is distributed under the GNU General
# Public License, version 3 or later.

"""提供 PeppyMeter 的原生 Pygame 右键菜单。"""

import os

import pygame


class MeterContextMenu(object):
    """绘制皮肤操作菜单，并把鼠标选择转换为应用动作。"""

    MENU_WIDTH = 250
    ROW_HEIGHT = 34
    SUBMENU_WIDTH = 150
    SUBMENU_ROW_HEIGHT = 30
    PADDING = 3

    def __init__(self, resolutions, interval_seconds=20):
        self.resolutions = list(resolutions)
        self.interval_seconds = interval_seconds
        self.row_height = self.ROW_HEIGHT
        self.is_open = False
        self.submenu_open = False
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.submenu_rect = pygame.Rect(0, 0, 0, 0)
        self.window_size = (0, 0)
        self.hovered_row = None
        self.hovered_submenu_row = None
        self.font = None

    def open_at(self, position, window_size):
        """在鼠标位置打开菜单，并限制菜单留在窗口范围内。"""
        self.window_size = window_size
        window_width, window_height = window_size
        width = min(self.MENU_WIDTH, window_width)
        height = min(self.PADDING * 2 + 5 * self.ROW_HEIGHT, window_height)
        left = max(0, min(position[0], window_width - width))
        top = max(0, min(position[1], window_height - height))
        self.rect = pygame.Rect(left, top, width, height)
        self.is_open = True
        self.submenu_open = False
        self.hovered_row = 0
        self.hovered_submenu_row = None

    def close(self):
        """关闭菜单及分辨率子菜单。"""
        self.is_open = False
        self.submenu_open = False
        self.hovered_row = None
        self.hovered_submenu_row = None

    def handle_event(self, event):
        """处理鼠标移动和点击，返回动作名或分辨率选择。"""
        if not self.is_open:
            return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            return None

        if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return None

        if self.submenu_open and self.submenu_rect.collidepoint(event.pos):
            row = self._submenu_row_at(event.pos)
            if row is not None and row < len(self.resolutions):
                resolution = self.resolutions[row][1]
                self.close()
                return ("resolution", resolution)

        row = self._main_row_at(event.pos)
        if row == 0:
            self._open_resolution_submenu()
            return None
        if row in (1, 2, 3, 4):
            actions = {1: "random_now", 2: "toggle_timed", 3: "previous", 4: "next"}
            self.close()
            return actions[row]

        self.close()
        return None

    def _main_row_at(self, position):
        if not self.rect.collidepoint(position):
            return None
        row = (position[1] - self.rect.top - self.PADDING) // self.ROW_HEIGHT
        return row if 0 <= row < 5 else None

    def _submenu_row_at(self, position):
        if not self.submenu_rect.collidepoint(position):
            return None
        row = (position[1] - self.submenu_rect.top - self.PADDING) // self.SUBMENU_ROW_HEIGHT
        return row if 0 <= row < len(self.resolutions) else None

    def _open_resolution_submenu(self):
        window_width, window_height = self.window_size
        height = self.PADDING * 2 + len(self.resolutions) * self.SUBMENU_ROW_HEIGHT
        left = self.rect.right
        if left + self.SUBMENU_WIDTH > window_width:
            left = self.rect.left - self.SUBMENU_WIDTH
        left = max(0, min(left, window_width - self.SUBMENU_WIDTH))
        top = self.rect.top + self.PADDING
        top = max(0, min(top, window_height - height))
        self.submenu_rect = pygame.Rect(left, top, self.SUBMENU_WIDTH, height)
        self.submenu_open = True

    def _update_hover(self, position):
        self.hovered_row = self._main_row_at(position)
        if self.submenu_open and self.submenu_rect.collidepoint(position):
            self.hovered_submenu_row = self._submenu_row_at(position)
            return
        self.hovered_submenu_row = None
        if self.hovered_row == 0:
            self._open_resolution_submenu()
        elif not self.rect.collidepoint(position):
            self.submenu_open = False

    def draw(self, screen, timed_random_enabled=False, current_resolution=None):
        """在表盘表面上绘制菜单。"""
        if not self.is_open:
            return
        if self.font is None:
            pygame.font.init()
            # 直接加载 Windows 常见中文字体，系统字体枚举失败时退回 Pygame 内置字体。
            font_path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyh.ttc")
            try:
                self.font = pygame.font.Font(font_path, 16)
            except (OSError, pygame.error):
                try:
                    self.font = pygame.font.SysFont("Microsoft YaHei UI", 16)
                except Exception:
                    self.font = pygame.font.Font(None, 16)

        self._draw_panel(screen, self.rect)
        labels = [
            "切换分辨率",
            "立刻随机切换",
            "定时随机切换（{}秒） {}".format(
                self.interval_seconds, "✓" if timed_random_enabled else ""
            ),
            "手动切换上一个",
            "手动切换下一个",
        ]
        for row, label in enumerate(labels):
            row_top = self.rect.top + self.PADDING + row * self.ROW_HEIGHT
            self._draw_row(screen, self.rect, row_top, self.ROW_HEIGHT, label, row == self.hovered_row)
            if row == 0:
                arrow = self.font.render("›", True, (235, 238, 244))
                screen.blit(arrow, (self.rect.right - 20, row_top + 7))

        if self.submenu_open:
            self._draw_panel(screen, self.submenu_rect)
            for row, (label, _) in enumerate(self.resolutions):
                row_top = self.submenu_rect.top + self.PADDING + row * self.SUBMENU_ROW_HEIGHT
                checked = "✓ " if label == current_resolution else ""
                self._draw_row(
                    screen,
                    self.submenu_rect,
                    row_top,
                    self.SUBMENU_ROW_HEIGHT,
                    checked + label,
                    row == self.hovered_submenu_row,
                )

    def _draw_panel(self, screen, rect):
        pygame.draw.rect(screen, (34, 37, 43), rect)
        pygame.draw.rect(screen, (105, 111, 121), rect, 1)

    def _draw_row(self, screen, panel, top, height, label, hovered):
        row_rect = pygame.Rect(panel.left + 1, top, panel.width - 2, height)
        if hovered:
            pygame.draw.rect(screen, (67, 77, 92), row_rect)
        text = self.font.render(label, True, (242, 244, 247))
        screen.blit(text, (row_rect.left + 9, row_rect.top + (height - text.get_height()) // 2))
