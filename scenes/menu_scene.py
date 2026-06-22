import math
from pathlib import Path

import pygame

from config import (
    ENERGY_COLOR,
    GOAL_COLOR,
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from core.fonts import brand_font, ui_font
from core.input import is_cancel, is_confirm, is_down, is_left, is_no, is_right, is_save, is_up, is_yes
from core.sounds import SoundManager
from ui.menu_effects import (
    bubble_position_at_time as animated_bubble_position,
    default_menu_bubbles,
    draw_rising_bubbles,
    draw_underwater_gradient,
)
from entities.objects import WildSeed
from entities.player import Player


BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "underwater_menu_bg.png"
LEVEL_SAVE_PANEL = pygame.Rect(220, 70, 520, 400)
CONFIRM_PANEL = pygame.Rect(190, 150, 580, 210)
LEVEL_NAME_DISPLAY = {
    "Tutorial1": "教程一",
    "Tutorial2": "教程二",
    "Tutorial3": "教程三",
    "Tutorial4": "教程四",
    "Reef1": "荆棘礁一",
    "Empty": "空",
}


class MenuScene:
    def __init__(self, save_manager=None, progress_data=None, session_progress=None, session_dirty=False, sfx_volume=80):
        self.save_manager = save_manager
        self.session_progress = dict(session_progress) if session_progress else None
        self.session_dirty = session_dirty
        self.sound = SoundManager()
        self.sound.set_sfx_volume(sfx_volume)
        self.progress_data = progress_data or self.session_progress or self.default_progress_data()
        self.title_font = brand_font(82)
        self.subtitle_font = self.make_font(21)
        self.tab_font = self.make_font(23)
        self.small_font = self.make_font(16)
        self.settings_font = self.make_font(18)
        self.mode = self.progress_data.get("open_mode", "main")
        self.selected = 0
        self.settings_index = 0
        self.level_selected = 0
        self.load_selected = 0
        self.level_hovered = None
        self.load_message = self.progress_data.get("load_message", "")
        self.map_message = self.progress_data.get("map_message", "")
        self.time = 0.0
        self.music_volume = 80
        self.sfx_volume = sfx_volume
        self.restart_hint_enabled = self.progress_data.get("restart_hint_enabled", True)
        self.background_image = self.load_background_image()
        self.bubbles = default_menu_bubbles()
        self.main_tabs = [
            ("继续游戏", "continue"),
            ("开始新游戏", "start_game"),
            ("读取存档", "load"),
            ("设置", "settings"),
            ("退出", "quit"),
        ]
        self.all_level_tabs = [
            ("初生海 - 1", 0),
            ("初生海 - 2", 1),
            ("初生海 - 3", 2),
            ("初生海 - 4", 3),
            ("荆棘礁 - 1", 4),
        ]
        self.all_level_descriptions = [
            "学习泡泡的移动路线，抵达安全的叶子。",
            "练习释放种子，并在开阔水域收集自由泡泡。",
            "穿过墙体和尖刺，用分裂泡泡调整浮力。",
            "利用气泡喷口补充泡泡，同时保留足够的种子。",
            "狭窄路线、侧向尖刺和分裂时机交织在一起。",
        ]
        self.unlock_seed_cost = 4
        self.unlock_animation_interval = 0.45
        self.unlock_confirmation = ""
        self.unlock_status_message = ""
        self.unlock_player = None
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = 0.0
        self.unlock_failed = False
        self.save_message = ""
        self.save_flow = "choose_action"
        self.save_action_index = 0
        self.save_slot_index = self.progress_data.get("slot_index", 0) if self.progress_data.get("slot_index") is not None else 0
        self.save_forbid_current_slot = False
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.save_name_input = self.default_save_name(self.save_slot_index)
        self.confirm_message = ""
        self.confirm_action = None
        self.confirm_return_mode = "main"
        self.confirm_save_enabled = False
        self.confirm_selected = "yes"
        self.level_save_return_mode = "levels"
        self.level_save_base_mode = "levels"
        self.level_save_continue_after_save = False
        self.refresh_progress_state()

    def make_font(self, size):
        return ui_font(size)

    def make_cjk_font(self, size):
        return self.make_font(size)

    def load_background_image(self):
        if not BACKGROUND_PATH.exists():
            return None
        try:
            image = pygame.image.load(str(BACKGROUND_PATH))
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def level_star_count(self, level_index):
        stars = self.progress_data.get("stars_by_level", {})
        if level_index in stars:
            return stars[level_index]
        return stars.get(str(level_index))

    def draw_small_star(self, surface, center, outer_radius, color, filled=True):
        inner_radius = outer_radius * 0.46
        points = []
        for index in range(10):
            angle = -math.pi / 2 + index * (math.pi / 5)
            radius = outer_radius if index % 2 == 0 else inner_radius
            points.append(
                (
                    center[0] + math.cos(angle) * radius,
                    center[1] + math.sin(angle) * radius,
                )
            )
        if filled:
            pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, color, points, 2)

    def refresh_progress_state(self):
        self.main_tabs = self.build_main_tabs()
        self.current_region = self.progress_data.get("current_region", "nursery")
        self.viewed_region = self.progress_data.get("viewed_region", self.current_region)
        self.thorn_reef_unlocked = self.progress_data.get("thorn_reef_unlocked", False)
        self.latest_level_index = min(
            self.progress_data.get("unlocked_levels", 0),
            len(self.all_level_tabs) - 1,
        )
        self.visible_level_indices = self.region_level_indices()
        current_level_index = self.progress_data.get("current_level_index", self.visible_level_indices[0])
        if current_level_index not in self.visible_level_indices:
            current_level_index = "gate" if self.show_region_gate() else self.visible_level_indices[0]
        self.level_selected = current_level_index
        self.selected = min(self.selected, len(self.main_tabs) - 1)

    def build_main_tabs(self):
        tabs = []
        if self.has_continue_progress():
            tabs.append(("继续游戏", "continue"))
        tabs.append(("开始新游戏", "start_game"))
        tabs.extend(
            [
                ("读取存档", "load"),
                ("设置", "settings"),
                ("退出", "quit"),
            ]
        )
        return tabs

    def has_continue_progress(self):
        return self.session_progress is not None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.mode == "level_save" and self.save_editing:
                    action = self.handle_level_save_text_input(event)
                    if action:
                        return action
                else:
                    action = self.handle_key(event)
                    if action:
                        return action
            elif event.type == pygame.MOUSEMOTION:
                self.update_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self.handle_click(event.pos)
                if action:
                    return action
        return None

    def handle_key(self, key):
        if self.mode == "main":
            if is_up(key):
                self.selected = (self.selected - 1) % len(self.main_tabs)
                self.sound.play("menu_move")
            elif is_down(key):
                self.selected = (self.selected + 1) % len(self.main_tabs)
                self.sound.play("menu_move")
            elif is_confirm(key):
                self.sound.play("menu_select")
                return self.activate_main_tab(self.selected)
        elif self.mode == "levels":
            if is_cancel(key):
                self.mode = "main"
                self.map_message = ""
            elif is_left(key):
                self.sound.play("menu_move")
                if not self.try_switch_region_page(-1):
                    self.move_level_selection(-1)
            elif is_right(key):
                self.sound.play("menu_move")
                if not self.try_switch_region_page(1):
                    self.move_level_selection(1)
            elif is_save(key):
                self.sound.play("menu_select")
                self.begin_level_save()
            elif is_confirm(key):
                self.sound.play("menu_select")
                return self.activate_map_selection()
        elif self.mode == "level_save":
            return self.handle_level_save_key(key)
        elif self.mode == "confirm":
            if is_cancel(key):
                self.cancel_confirmation()
                self.sound.play("menu_move")
            elif is_left(key) or is_right(key):
                self.move_confirmation_selection(-1 if is_left(key) else 1)
                self.sound.play("menu_move")
            elif self.confirm_save_available():
                if is_yes(key):
                    self.confirm_selected = "yes"
                    self.begin_confirmation_save()
                    self.sound.play("menu_select")
                elif is_no(key):
                    self.confirm_selected = "no"
                    self.sound.play("menu_select")
                    return self.confirm_pending_action()
                elif is_confirm(key):
                    self.sound.play("menu_select")
                    return self.activate_confirmation_selection()
            elif is_confirm(key) or is_yes(key):
                self.sound.play("menu_select")
                return self.confirm_pending_action()
        elif self.mode == "load":
            if is_cancel(key):
                self.mode = "main"
                self.load_message = ""
                self.sound.play("menu_select")
            elif is_up(key):
                self.load_selected = (self.load_selected - 1) % 3
                self.load_message = ""
                self.sound.play("menu_move")
            elif is_down(key):
                self.load_selected = (self.load_selected + 1) % 3
                self.load_message = ""
                self.sound.play("menu_move")
            elif is_confirm(key):
                self.sound.play("menu_select")
                return self.activate_load_slot(self.load_selected)
        elif self.mode == "settings":
            if is_cancel(key):
                self.mode = "main"
                self.sound.play("menu_select")
            elif is_up(key):
                self.settings_index = (self.settings_index - 1) % self.settings_count()
                self.sound.play("menu_move")
            elif is_down(key):
                self.settings_index = (self.settings_index + 1) % self.settings_count()
                self.sound.play("menu_move")
            elif is_left(key):
                self.sound.play("menu_move")
                if self.settings_index == 0:
                    self.music_volume = max(0, self.music_volume - 10)
                elif self.settings_index == 1:
                    self.sfx_volume = max(0, self.sfx_volume - 10)
                    self.sound.set_sfx_volume(self.sfx_volume)
                else:
                    self.toggle_restart_hint_setting()
            elif is_right(key):
                self.sound.play("menu_move")
                if self.settings_index == 0:
                    self.music_volume = min(100, self.music_volume + 10)
                elif self.settings_index == 1:
                    self.sfx_volume = min(100, self.sfx_volume + 10)
                    self.sound.set_sfx_volume(self.sfx_volume)
                else:
                    self.toggle_restart_hint_setting()
            elif is_confirm(key) and self.settings_index == 2:
                self.sound.play("menu_select")
                self.toggle_restart_hint_setting()
        elif self.mode == "unlock_confirm":
            if is_cancel(key):
                self.mode = "levels"
                self.unlock_confirmation = ""
                self.sound.play("menu_select")
            elif is_confirm(key) or is_yes(key):
                self.sound.play("menu_select")
                self.start_region_unlock()
            elif is_no(key):
                self.mode = "levels"
                self.unlock_confirmation = ""
                self.sound.play("menu_select")
        elif self.mode == "unlock_result":
            if is_confirm(key) or key == pygame.K_ESCAPE:
                if self.unlock_failed:
                    self.reset_to_nursery_start()
                self.mode = "levels"
                self.unlock_status_message = ""
                self.sound.play("menu_select")
        return None

    def activate_main_tab(self, index):
        action = self.main_tabs[index][1]
        if action == "start_game":
            fresh_progress = self.default_progress_data()
            pending_action = {
                "type": "intro",
                "start_action": self.build_level_map_action(fresh_progress),
            }
            if self.should_warn_about_losing_progress():
                self.begin_confirmation(
                    pending_action,
                    "当前进度尚未保存。开始新游戏会丢弃它。",
                    allow_save=True,
                )
                return None
            return pending_action
        if action == "continue":
            if not self.session_progress:
                self.load_message = "没有可继续的当前进度"
                return None
            return self.build_level_map_action(self.session_progress)
        if action == "load":
            self.mode = "load"
            self.load_message = ""
        elif action == "settings":
            self.mode = "settings"
        elif action == "quit":
            return self.request_quit_action()
        return None

    def build_level_map_action(self, progress_data):
        progress = dict(progress_data or {})
        progress["open_mode"] = "levels"
        progress["has_started_game"] = True
        return {
            "type": "menu",
            "progress_data": progress,
        }

    def should_warn_about_losing_progress(self):
        return self.session_progress is not None and self.session_dirty

    def begin_confirmation(self, action, message, allow_save=False):
        self.confirm_action = action
        self.confirm_message = message
        self.confirm_return_mode = self.mode
        self.confirm_save_enabled = allow_save
        self.confirm_selected = "no" if allow_save else "yes"
        self.mode = "confirm"

    def cancel_confirmation(self):
        self.mode = self.confirm_return_mode
        self.confirm_action = None
        self.confirm_message = ""
        self.confirm_save_enabled = False
        self.confirm_selected = "yes"

    def confirm_pending_action(self):
        action = self.confirm_action
        self.confirm_action = None
        self.confirm_message = ""
        self.confirm_save_enabled = False
        self.confirm_selected = "yes"
        self.mode = self.confirm_return_mode
        return action

    def handle_level_save_text_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.save_name_input = self.save_name_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.save_editing = False
            self.save_message = "已取消保存"
            self.save_name_input = self.slot_display_name(self.save_slot_index)
            self.sound.play("menu_select")
        elif event.key == pygame.K_RETURN:
            if self.save_to_slot(self.save_slot_index):
                self.sound.play("menu_select")
                return self.close_level_save(show_message=True, saved=True)
        elif event.unicode and event.unicode.isprintable() and len(self.save_name_input) < 18:
            self.save_name_input += event.unicode
        return None

    def confirm_save_available(self):
        return self.confirm_save_enabled and self.should_warn_about_losing_progress()

    def play_menu_move_if_changed(self, previous, current):
        if previous != current:
            self.sound.play("menu_move")

    def begin_confirmation_save(self):
        self.begin_level_save(
            return_mode="confirm",
            base_mode=self.confirm_return_mode,
            continue_after_save=True,
        )

    def toggle_confirmation_selection(self):
        self.confirm_selected = "no" if self.confirm_selected == "yes" else "yes"

    def move_confirmation_selection(self, direction):
        if direction < 0:
            self.confirm_selected = "no"
        elif direction > 0:
            self.confirm_selected = "yes"

    def activate_confirmation_selection(self):
        if self.confirm_save_available() and self.confirm_selected == "yes":
            self.begin_confirmation_save()
            return None
        return self.confirm_pending_action()

    def request_quit_action(self):
        if self.should_warn_about_losing_progress():
            self.begin_confirmation(
                {"type": "quit"},
                "当前进度尚未保存。仍要退出吗？",
                allow_save=True,
            )
            return None
        return {"type": "quit"}

    def update_hover(self, pos):
        if self.mode == "confirm":
            if self.confirm_save_available():
                previous = self.confirm_selected
                if self.confirm_yes_rect().collidepoint(pos):
                    self.confirm_selected = "yes"
                elif self.confirm_no_rect().collidepoint(pos):
                    self.confirm_selected = "no"
                self.play_menu_move_if_changed(previous, self.confirm_selected)
            return
        if self.mode == "level_save":
            if self.save_flow == "choose_action":
                for index, _ in enumerate(self.save_action_options()):
                    if self.level_save_action_rect(index).collidepoint(pos):
                        previous = self.save_action_index
                        self.save_action_index = index
                        self.play_menu_move_if_changed(previous, self.save_action_index)
                        return
            else:
                for index in range(3):
                    if self.level_save_slot_rect(index).collidepoint(pos):
                        if not self.current_slot_locked(index):
                            previous = self.save_slot_index
                            self.save_slot_index = index
                            self.play_menu_move_if_changed(previous, self.save_slot_index)
                        return
            return
        if self.mode == "levels":
            level_index = self.level_node_at_pos(pos)
            self.level_hovered = level_index
            if level_index == "gate":
                previous = self.level_selected
                self.level_selected = "gate"
                self.play_menu_move_if_changed(previous, self.level_selected)
                return
            if level_index is not None and self.is_level_unlocked(level_index):
                previous = self.level_selected
                self.level_selected = level_index
                self.play_menu_move_if_changed(previous, self.level_selected)
            return
        if self.mode == "load":
            self.level_hovered = None
            for index in range(3):
                if self.load_slot_rect(index).collidepoint(pos):
                    previous = self.load_selected
                    self.load_selected = index
                    self.play_menu_move_if_changed(previous, self.load_selected)
                    return

        if self.mode == "settings":
            setting_index = self.setting_at_pos(pos)
            if setting_index is not None:
                previous = self.settings_index
                self.settings_index = setting_index
                self.play_menu_move_if_changed(previous, self.settings_index)
                return

        self.level_hovered = None

        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "main":
                    previous = self.selected
                    self.selected = index
                    self.play_menu_move_if_changed(previous, self.selected)
                return

    def handle_click(self, pos):
        if self.mode == "confirm":
            if self.confirm_close_rect().collidepoint(pos):
                self.cancel_confirmation()
                self.sound.play("menu_move")
                return None
            if self.confirm_save_available():
                if self.confirm_yes_rect().collidepoint(pos):
                    self.confirm_selected = "yes"
                    self.begin_confirmation_save()
                    self.sound.play("menu_select")
                    return None
                if self.confirm_no_rect().collidepoint(pos):
                    self.confirm_selected = "no"
                    self.sound.play("menu_select")
                    return self.confirm_pending_action()
                return None
            if self.confirm_yes_rect().collidepoint(pos):
                self.sound.play("menu_select")
                return self.confirm_pending_action()
            if self.confirm_no_rect().collidepoint(pos):
                self.cancel_confirmation()
                self.sound.play("menu_select")
            return None
        if self.mode == "level_save":
            return self.handle_level_save_click(pos)
        if self.mode == "levels":
            if self.level_save_rect().collidepoint(pos):
                self.sound.play("menu_select")
                self.begin_level_save()
                return None
            if self.level_back_rect().collidepoint(pos):
                self.sound.play("menu_select")
                self.mode = "main"
                self.map_message = ""
                return None
            hit = self.level_node_at_pos(pos)
            if hit == "gate":
                self.sound.play("menu_select")
                return self.begin_region_unlock()
            if hit is not None:
                self.sound.play("menu_select")
            return self.activate_level_node(hit)
        if self.mode == "load":
            if self.load_back_rect().collidepoint(pos):
                self.sound.play("menu_select")
                self.mode = "main"
                self.load_message = ""
                return None
            for index in range(3):
                if self.load_slot_rect(index).collidepoint(pos):
                    self.load_selected = index
                    self.sound.play("menu_select")
                    return self.activate_load_slot(index)
            return None

        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "main":
                    self.selected = index
                    self.sound.play("menu_select")
                    return self.activate_main_tab(index)

        if self.mode in ("levels", "settings", "unlock_confirm", "unlock_result"):
            back_rect = pygame.Rect(44, 38, 116, 42)
            if back_rect.collidepoint(pos):
                self.sound.play("menu_select")
                self.mode = "main"
                return None
        if self.mode == "settings":
            setting_index = self.setting_at_pos(pos)
            if setting_index is not None:
                self.settings_index = setting_index
                self.sound.play("menu_select")
                if setting_index == 2:
                    self.toggle_restart_hint_setting()
        return None

    def handle_level_save_click(self, pos):
        if self.save_flow == "choose_action":
            for index, (_, choice) in enumerate(self.save_action_options()):
                if self.level_save_action_rect(index).collidepoint(pos):
                    self.save_action_index = index
                    self.sound.play("menu_select")
                    return self.choose_level_save_action(choice)
            return None

        for index in range(3):
            if self.level_save_slot_rect(index).collidepoint(pos):
                self.sound.play("menu_select")
                self.select_level_save_slot(index, begin_edit_on_repeat=True)
                return None
        return None

    def default_progress_data(self):
        return {
            "current_level_index": 0,
            "latest_level_index": 0,
            "unlocked_levels": 0,
            "player_bubbles": 1,
            "player_seeds": 0,
            "seed_total": 0,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
            "restart_hint_enabled": True,
            "has_started_game": False,
        }

    def toggle_restart_hint_setting(self):
        self.restart_hint_enabled = not self.restart_hint_enabled
        self.progress_data = dict(self.progress_data)
        self.progress_data["restart_hint_enabled"] = self.restart_hint_enabled
        if self.progress_data.get("has_started_game"):
            self.mark_progress_dirty()

    def region_level_indices(self):
        if self.viewed_region == "thorn_reef":
            return [4]
        return [0, 1, 2, 3]

    @property
    def level_tabs(self):
        return self.visible_level_tabs()

    def visible_level_tabs(self):
        return [self.all_level_tabs[index] for index in self.visible_level_indices]

    def visible_level_descriptions(self):
        return [self.all_level_descriptions[index] for index in self.visible_level_indices]

    def show_region_gate(self):
        return self.viewed_region == "nursery" and not self.thorn_reef_unlocked and self.latest_level_index >= 3

    def selectable_map_items(self):
        items = list(self.visible_level_indices)
        if self.show_region_gate():
            items.append("gate")
        return items

    def move_level_selection(self, delta):
        items = self.selectable_map_items()
        current = self.level_selected if self.level_selected in items else items[0]
        index = items.index(current)
        self.level_selected = items[(index + delta) % len(items)]

    def try_switch_region_page(self, direction):
        if direction < 0:
            if self.viewed_region == "thorn_reef" and self.level_selected == 4:
                self.viewed_region = "nursery"
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = self.visible_level_indices[-1]
                self.level_hovered = None
                self.map_message = "初生海"
                return True
            return False

        if self.viewed_region == "nursery":
            if self.thorn_reef_unlocked and self.level_selected == self.visible_level_indices[-1]:
                self.viewed_region = "thorn_reef"
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = 4
                self.level_hovered = None
                self.map_message = "荆棘礁"
                return True
            if self.show_region_gate() and self.level_selected == self.visible_level_indices[-1]:
                self.level_selected = "gate"
                self.map_message = f"消耗 {self.unlock_seed_cost} 颗种子解锁荆棘礁"
                return True
        return False

    def activate_map_selection(self):
        if self.level_selected == "gate":
            return self.begin_region_unlock()
        return self.activate_level_node(self.level_selected)

    def activate_level_node(self, level_index):
        if level_index is None or not self.is_level_playable(level_index):
            if level_index is not None and level_index in self.visible_level_indices:
                self.map_message = "进入荆棘礁后，无法从此处返回初生海"
            return None
        self.level_selected = level_index
        return {
            "type": "start",
            "level": self.all_level_tabs[level_index][1],
            "slot_index": self.progress_data.get("slot_index"),
            "save_data": self.progress_data or None,
        }

    def activate_load_slot(self, slot_index):
        if not self.save_manager:
            self.load_message = "存档系统不可用"
            return None
        slot = self.save_manager.get_slot(slot_index)
        if not slot:
            self.load_message = f"存档 {slot_index + 1} 为空"
            return None
        pending_action = self.build_level_map_action({**slot, "slot_index": slot_index})
        if self.should_warn_about_losing_progress():
            self.begin_confirmation(
                pending_action,
                "当前进度尚未保存。读取其他存档会丢弃它。",
                allow_save=True,
            )
            return None
        return pending_action

    def handle_level_save_key(self, key):
        if self.save_flow == "choose_action":
            options = self.save_action_options()
            if is_up(key) or is_left(key):
                self.save_action_index = (self.save_action_index - 1) % len(options)
                self.sound.play("menu_move")
            elif is_down(key) or is_right(key):
                self.save_action_index = (self.save_action_index + 1) % len(options)
                self.sound.play("menu_move")
            elif is_cancel(key):
                self.close_level_save()
                self.sound.play("menu_select")
            elif is_confirm(key):
                _, choice = options[self.save_action_index]
                self.sound.play("menu_select")
                return self.choose_level_save_action(choice)
            return None

        if self.save_editing:
            if key == pygame.K_BACKSPACE:
                self.save_name_input = self.save_name_input[:-1]
            elif key == pygame.K_ESCAPE:
                self.save_editing = False
                self.save_message = "已取消保存"
                self.save_name_input = self.slot_display_name(self.save_slot_index)
            elif key == pygame.K_RETURN:
                if self.save_to_slot(self.save_slot_index):
                    return self.close_level_save(show_message=True, saved=True)
            return None

        if is_up(key):
            self.move_save_slot_selection(-1)
            self.sound.play("menu_move")
        elif is_down(key):
            self.move_save_slot_selection(1)
            self.sound.play("menu_move")
        elif is_cancel(key):
            self.close_level_save()
            self.sound.play("menu_select")
        elif is_confirm(key):
            self.begin_save_name_edit()
            self.sound.play("menu_select")
        return None

    def choose_level_save_action(self, choice):
        if choice == "update_current":
            self.save_slot_index = self.progress_data.get("slot_index")
            self.save_name_input = self.slot_display_name(self.save_slot_index)
            if self.save_to_slot(self.save_slot_index):
                return self.close_level_save(show_message=True, saved=True)
            return None
        self.prepare_level_save_as_new()
        return None

    def prepare_level_save_as_new(self):
        current_slot_index = self.progress_data.get("slot_index")
        self.save_flow = "choose_slot"
        self.save_forbid_current_slot = current_slot_index is not None
        self.save_slot_index = 0 if current_slot_index is None else (current_slot_index + 1) % 3
        if self.save_forbid_current_slot and self.save_slot_index == current_slot_index:
            self.move_save_slot_selection(1)
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

    def current_slot_locked(self, slot_index):
        return (
            self.save_forbid_current_slot
            and self.progress_data.get("slot_index") is not None
            and slot_index == self.progress_data.get("slot_index")
        )

    def select_level_save_slot(self, slot_index, begin_edit_on_repeat=False):
        if self.current_slot_locked(slot_index):
            return
        already_selected = self.save_slot_index == slot_index
        self.save_slot_index = slot_index
        if self.save_editing:
            return
        if begin_edit_on_repeat and already_selected:
            self.begin_save_name_edit()
        else:
            self.save_name_input = self.slot_display_name(slot_index)
            self.save_message = ""

    def is_level_unlocked(self, level_index):
        return level_index in self.visible_level_indices and level_index <= self.latest_level_index

    def is_level_playable(self, level_index):
        if not self.is_level_unlocked(level_index):
            return False
        if self.current_region == "thorn_reef" and level_index < 4:
            return False
        return True

    def level_node_centers(self):
        count = len(self.visible_level_indices)
        if count <= 1:
            return [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]

        if self.viewed_region == "thorn_reef":
            route = [(520, 306)]
        else:
            route = [
                (128, 388),
                (342, 302),
                (586, 370),
                (768, 288),
            ]
        if count <= len(route):
            return route[:count]

        centers = []
        for index in range(count):
            t = index / (count - 1)
            position = t * (len(route) - 1)
            left = min(int(position), len(route) - 2)
            local_t = position - left
            x1, y1 = route[left]
            x2, y2 = route[left + 1]
            centers.append((
                int(x1 + (x2 - x1) * local_t),
                int(y1 + (y2 - y1) * local_t),
            ))
        return centers

    def level_node_at_pos(self, pos):
        for index, center in enumerate(self.level_node_centers()):
            if math.dist(pos, center) <= 24:
                return self.visible_level_indices[index]
        if self.show_region_gate() and math.dist(pos, self.region_gate_center()) <= 28:
            return "gate"
        return None

    def update(self, dt):
        self.time += dt
        if self.mode == "unlock_anim":
            self.update_region_unlock(dt)
        if self.mode == "level_save" and self.save_editing:
            self.save_cursor_timer += dt

    def draw(self, screen):
        if self.mode == "confirm":
            self.draw_confirm_base(screen)
            self.draw_confirm_overlay(screen)
            return
        if self.mode == "levels":
            self.draw_levels(screen)
            return
        if self.mode == "load":
            self.draw_load(screen)
            return
        if self.mode in ("unlock_confirm", "unlock_anim", "unlock_result"):
            self.draw_levels(screen)
            self.draw_unlock_overlay(screen)
            return
        if self.mode == "level_save":
            self.draw_level_save_base(screen)
            self.draw_level_save_overlay(screen)
            return

        self.draw_background(screen)
        self.draw_title(screen)
        if self.mode == "main":
            self.draw_main(screen)
        else:
            self.draw_settings(screen)

    def draw_level_save_base(self, screen):
        if self.level_save_base_mode == "levels":
            self.draw_levels(screen)
            return
        if self.level_save_base_mode == "load":
            self.draw_load(screen)
            return
        if self.level_save_base_mode in ("unlock_confirm", "unlock_anim", "unlock_result"):
            self.draw_levels(screen)
            self.draw_unlock_overlay(screen)
            return

        self.draw_background(screen)
        self.draw_title(screen)
        if self.level_save_base_mode == "settings":
            self.draw_settings(screen)
        else:
            self.draw_main(screen)

    def draw_confirm_base(self, screen):
        if self.confirm_return_mode == "levels":
            self.draw_levels(screen)
            return
        if self.confirm_return_mode == "load":
            self.draw_load(screen)
            return
        if self.confirm_return_mode in ("unlock_confirm", "unlock_anim", "unlock_result"):
            self.draw_levels(screen)
            self.draw_unlock_overlay(screen)
            return

        self.draw_background(screen)
        self.draw_title(screen)
        if self.confirm_return_mode == "settings":
            self.draw_settings(screen)
        else:
            self.draw_main(screen)

    def draw_background(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
            water_tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            water_tint.fill((0, 24, 34, 42))
            screen.blit(water_tint, (0, 0))
        else:
            draw_underwater_gradient(screen)

        draw_rising_bubbles(screen, self.bubbles, self.time)

    def bubble_position_at_time(self, bubble, elapsed):
        return animated_bubble_position(bubble, elapsed)

    def draw_title(self, screen):
        title = self.title_font.render("Bubbles", True, WHITE)
        shadow = self.title_font.render("Bubbles", True, (30, 95, 113))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 78)))

        subtitle = self.subtitle_font.render("携生命种子，从深海回到陆地", True, TEXT_COLOR)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)))

    def draw_main(self, screen):
        for index, (label, _) in enumerate(self.main_tabs):
            rect = self.main_tab_rect(index)
            self.draw_glass_tab(screen, rect, label, index == self.selected)

        hint_text = "方向键或 W/S 选择，回车确认"
        if self.load_message:
            hint_text = self.load_message
        hint = self.small_font.render(hint_text, True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_levels(self, screen):
        self.draw_level_map_picture(screen)
        self.draw_level_map_route(screen)
        self.draw_level_map_nodes(screen)
        self.draw_region_gate(screen)
        self.draw_level_hover_panel(screen)
        self.draw_level_map_save_button(screen)
        self.draw_level_map_back_button(screen)

        title = self.tab_font.render("关卡选择", True, (242, 252, 226))
        shadow = self.tab_font.render("关卡选择", True, (11, 35, 55))
        shadow.set_alpha(125)
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 1, 57)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 55)))

        subtitle_text = self.map_message or ("荆棘礁" if self.viewed_region == "thorn_reef" else "初生海")
        subtitle = self.subtitle_font.render(subtitle_text, True, (199, 222, 230))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 116)))

    def draw_load(self, screen):
        self.draw_background(screen)
        self.draw_title(screen)
        heading = self.subtitle_font.render("读取存档", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 190)))

        for index in range(3):
            rect = self.load_slot_rect(index)
            selected = index == self.load_selected
            self.draw_glass_panel(screen, rect, selected)
            name, level_name, seed_total = self.load_slot_summary(index)
            title = self.tab_font.render(f"存档 {index + 1}: {name}", True, WHITE if selected else TEXT_COLOR)
            meta = self.small_font.render(f"{self.display_level_name(level_name)}  |  种子 {seed_total}", True, WHITE if selected else MUTED_TEXT)
            screen.blit(title, title.get_rect(midleft=(rect.left + 20, rect.centery - 12)))
            screen.blit(meta, meta.get_rect(midleft=(rect.left + 20, rect.centery + 14)))

        self.draw_load_back_button(screen)
        hint_text = self.load_message or "选择一个存档，读取后进入关卡地图"
        hint = self.small_font.render(hint_text, True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_level_map_picture(self, screen):
        self.draw_background(screen)

        beams = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in (30, 360, 710):
            pygame.draw.polygon(
                beams,
                (160, 226, 248, 20),
                [(x, 0), (x + 94, 0), (x + 198, SCREEN_HEIGHT), (x + 62, SCREEN_HEIGHT)],
            )
        screen.blit(beams, (0, 0))
        depth = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        depth.fill((0, 18, 28, 34))
        screen.blit(depth, (0, 0))

    def draw_level_map_route(self, screen):
        centers = self.level_node_centers()
        if len(centers) < 2:
            return

        for index, (start, end) in enumerate(zip(centers, centers[1:])):
            color = (229, 72, 58) if index < self.latest_level_index else (105, 116, 122)
            self.draw_dotted_line(screen, start, end, color)
        if self.show_region_gate() and centers:
            gate_color = (247, 188, 63) if self.latest_level_index >= 3 else (105, 116, 122)
            self.draw_dotted_line(screen, centers[-1], self.region_gate_center(), gate_color)

    def draw_dotted_line(self, screen, start, end, color):
        distance = math.dist(start, end)
        if distance <= 0:
            return
        steps = max(1, int(distance / 22))
        for step in range(1, steps):
            t = step / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            pygame.draw.circle(screen, (12, 31, 44), (int(x), int(y)), 8)
            pygame.draw.circle(screen, color, (int(x), int(y)), 6)
            pygame.draw.circle(screen, (255, 238, 224, 170), (int(x - 2), int(y - 3)), 2)

    def draw_level_map_nodes(self, screen):
        for display_index, center in enumerate(self.level_node_centers()):
            self.draw_level_map_node(screen, self.visible_level_indices[display_index], center)

    def region_gate_center(self):
        return (906, 190)

    def draw_level_selection_glow(self, screen, center):
        glow = pygame.Surface((66, 66), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 240, 158, 66), (33, 33), 30)
        screen.blit(glow, (center[0] - 33, center[1] - 33))

    def draw_region_gate(self, screen):
        if not self.show_region_gate():
            return
        center = self.region_gate_center()
        selected = self.level_selected == "gate"
        unlocked = self.can_attempt_region_unlock()
        if selected:
            self.draw_level_selection_glow(screen, center)
        rim = (252, 252, 232) if selected else (230, 238, 230)
        fill = (247, 188, 63) if unlocked else (124, 137, 143)
        pygame.draw.circle(screen, (9, 28, 42), center, 22)
        pygame.draw.circle(screen, rim, center, 20)
        pygame.draw.circle(screen, fill, center, 17)
        lock_text = self.small_font.render("4", True, (9, 28, 42))
        screen.blit(lock_text, lock_text.get_rect(center=center))
        label = self.small_font.render("解锁荆棘礁", True, WHITE if unlocked else MUTED_TEXT)
        screen.blit(label, label.get_rect(center=(center[0], center[1] + 42)))

    def draw_level_map_node(self, screen, index, center):
        unlocked = self.is_level_unlocked(index)
        playable = self.is_level_playable(index)
        passed = index < self.latest_level_index
        selected = index == self.level_selected

        if selected and playable:
            self.draw_level_selection_glow(screen, center)

        rim = (252, 252, 232) if selected and playable else (230, 238, 230)
        fill = (230, 72, 62) if passed else (247, 188, 63)
        if not unlocked:
            fill = (124, 137, 143)
            rim = (177, 188, 192)
        elif not playable:
            fill = (92, 108, 116)
            rim = (160, 176, 182)

        pygame.draw.circle(screen, (9, 28, 42), center, 18)
        pygame.draw.circle(screen, rim, center, 16)
        pygame.draw.circle(screen, fill, center, 13)

        label, _ = self.all_level_tabs[index]
        if not unlocked:
            label_color = (143, 159, 166)
        elif not playable:
            label_color = (164, 176, 182)
        else:
            label_color = (238, 246, 235)
        text = self.tab_font.render(label, True, label_color)
        shadow = self.tab_font.render(label, True, (8, 27, 39))
        shadow.set_alpha(130)
        label_y = center[1] + 38
        if index == 1:
            label_y = center[1] + 34
        screen.blit(shadow, shadow.get_rect(center=(center[0] + 1, label_y + 1)))
        screen.blit(text, text.get_rect(center=(center[0], label_y)))

    def draw_level_hover_panel(self, screen):
        if self.level_hovered is None:
            return

        rect = self.level_hover_panel_rect()
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(panel, panel.get_rect(), selected=True)

        if self.level_hovered == "gate":
            title = self.tab_font.render("荆棘礁入口", True, WHITE)
            panel.blit(title, (24, 28))
            status = f"消耗 {self.unlock_seed_cost} 颗种子解锁"
            status_text = self.small_font.render(status, True, (184, 236, 255))
            panel.blit(status_text, (24, 58))
            description = "连续释放四颗种子后，泡泡必须仍然存活，才能进入下一片海域。"
            self.draw_wrapped_text(panel, description, pygame.Rect(24, 84, 270, 56), MUTED_TEXT, self.small_font)
        else:
            mini_rect = pygame.Rect(18, 24, 118, 92)
            self.draw_level_minimap(panel, mini_rect, self.level_hovered)

            label, _ = self.all_level_tabs[self.level_hovered]
            title = self.tab_font.render(label, True, WHITE)
            panel.blit(title, (154, 28))

            locked = not self.is_level_unlocked(self.level_hovered)
            playable = self.is_level_playable(self.level_hovered)
            if locked:
                status = "未解锁"
                status_color = MUTED_TEXT
            elif not playable:
                status = "已离开海域"
                status_color = (190, 200, 205)
            else:
                status = "可进入"
                status_color = (184, 236, 255)
            status_text = self.small_font.render(status, True, status_color)
            panel.blit(status_text, (154, 58))

            stars = self.level_star_count(self.level_hovered)
            if stars is not None:
                for index in range(3):
                    filled = index < int(stars)
                    color = (255, 221, 126) if filled else (120, 115, 96)
                    self.draw_small_star(panel, (174 + index * 28, 84), 9, color, filled=filled)
                description_top = 102
            else:
                description_top = 84

            description = self.all_level_descriptions[self.level_hovered]
            self.draw_wrapped_text(panel, description, pygame.Rect(154, description_top, 154, 56), MUTED_TEXT, self.small_font)
        screen.blit(panel, rect)

    def level_hover_panel_rect(self):
        panel_width = 334
        panel_height = 158
        margin = 24
        gap = 38

        center = self.level_hover_center()
        if center is None:
            return pygame.Rect(SCREEN_WIDTH - panel_width - margin, 164, panel_width, panel_height)

        x = center[0] + gap
        if x + panel_width + margin > SCREEN_WIDTH:
            x = center[0] - gap - panel_width
        x = max(margin, min(x, SCREEN_WIDTH - panel_width - margin))

        y = center[1] - panel_height // 2
        y = max(134, min(y, SCREEN_HEIGHT - panel_height - 64))
        return pygame.Rect(x, y, panel_width, panel_height)

    def level_hover_center(self):
        if self.level_hovered == "gate":
            return self.region_gate_center()
        if self.level_hovered in self.visible_level_indices:
            display_index = self.visible_level_indices.index(self.level_hovered)
            return self.level_node_centers()[display_index]
        return None

    def draw_level_minimap(self, surface, rect, level_index):
        self.draw_liquid_glass_surface(surface, rect, selected=False, radius=6)

        water_line = rect.bottom - 18
        pygame.draw.line(surface, (77, 151, 168), (rect.left + 8, water_line), (rect.right - 8, water_line), 2)
        start = (rect.left + 18, rect.bottom - 28)
        goal = (rect.right - 20, rect.top + 24)
        pygame.draw.circle(surface, (83, 188, 126), start, 7)
        pygame.draw.circle(surface, (223, 193, 92), goal, 7)

        if level_index == 0:
            pygame.draw.arc(surface, (184, 236, 255), (rect.left + 24, rect.top + 20, 62, 48), 0.15, 2.8, 3)
            pygame.draw.circle(surface, (139, 244, 166), (rect.left + 64, rect.top + 36), 4)
        elif level_index == 1:
            pygame.draw.line(surface, (184, 236, 255), (rect.left + 22, rect.top + 58), (rect.right - 28, rect.top + 42), 3)
            pygame.draw.circle(surface, (238, 248, 255), (rect.left + 64, rect.top + 64), 6, 2)
        else:
            pygame.draw.rect(surface, (28, 77, 86), (rect.left + 38, rect.top + 18, 12, 58), border_radius=3)
            pygame.draw.rect(surface, (28, 77, 86), (rect.left + 70, rect.top + 44, 36, 10), border_radius=3)
            for x in (rect.left + 58, rect.left + 78, rect.left + 98):
                pygame.draw.polygon(surface, (219, 228, 220), [(x, rect.top + 40), (x + 6, rect.top + 54), (x - 6, rect.top + 54)])

    def draw_wrapped_text(self, surface, text, rect, color, font):
        words = self.wrap_units(text)
        line = ""
        y = rect.top
        for word in words:
            candidate = word if not line else f"{line}{word}"
            if font.size(candidate)[0] <= rect.width:
                line = candidate
                continue
            if line and word in "，。！？；：、）】》”’":
                line = candidate
                continue
            if line:
                surface.blit(font.render(line, True, color), (rect.left, y))
                y += font.get_linesize()
            line = word
            if y + font.get_linesize() > rect.bottom:
                return
        if line and y + font.get_linesize() <= rect.bottom:
            surface.blit(font.render(line, True, color), (rect.left, y))

    def wrap_units(self, text):
        if " " not in text:
            return list(text)
        units = []
        words = text.split(" ")
        for index, word in enumerate(words):
            if index:
                units.append(" ")
            units.append(word)
        return units

    def level_back_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 164, SCREEN_HEIGHT - 48, 144, 38)

    def load_back_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 164, SCREEN_HEIGHT - 48, 144, 38)

    def load_slot_rect(self, index):
        return pygame.Rect(230, 240 + index * 86, 500, 62)

    def load_slot_summary(self, slot_index):
        slot = self.save_manager.get_slot(slot_index) if self.save_manager else None
        if not slot:
            return f"存档 {slot_index + 1}", "空", 0
        return (
            slot.get("name") or f"存档 {slot_index + 1}",
            self.display_level_name(slot.get("latest_level_name", "Empty")),
            slot.get("seed_total", 0),
        )

    def display_level_name(self, level_name):
        return LEVEL_NAME_DISPLAY.get(level_name, level_name)

    def draw_level_map_back_button(self, screen):
        rect = self.level_back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(surface, surface.get_rect(), selected=False)
        label = self.tab_font.render("返回", True, WHITE)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)

    def draw_level_map_save_button(self, screen):
        rect = self.level_save_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(surface, surface.get_rect(), selected=False)
        label = self.small_font.render("保存", True, WHITE)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)

    def draw_load_back_button(self, screen):
        rect = self.load_back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (178, 210, 220, 62), surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, (230, 246, 250, 190), surface.get_rect(), 2, border_radius=8)
        pygame.draw.rect(surface, (52, 82, 98, 170), surface.get_rect().inflate(-10, -8), border_radius=6)
        label = self.tab_font.render("返回", True, WHITE)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)

    def draw_level_save_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 170))
        screen.blit(overlay, (0, 0))

        panel = LEVEL_SAVE_PANEL
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)

        title = self.big_level_save_font().render("保存进度", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 48)))

        if self.save_flow == "choose_action":
            header = self.small_font.render("选择保存方式", True, TEXT_COLOR)
            surface.blit(header, (40, 124))
            options = self.save_action_options()
            for index, (label, _) in enumerate(options):
                rect = self.level_save_local_action_rect(index)
                selected = index == self.save_action_index
                fill = (27, 92, 110, 220) if selected else (17, 63, 82, 200)
                pygame.draw.rect(surface, fill, rect, border_radius=12)
                pygame.draw.rect(surface, (208, 246, 255) if selected else (96, 148, 160), rect, 2, border_radius=12)
                option_surface = self.small_font.render(label, True, WHITE if selected else TEXT_COLOR)
                surface.blit(option_surface, option_surface.get_rect(center=rect.center))
            hint = self.small_font.render("回车确认，Esc 返回", True, MUTED_TEXT)
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 344)))
        else:
            header_text = (
                "选择另一个存档位，按回车编辑名称"
                if not self.save_editing
                else "正在编辑名称，再按回车保存"
            )
            header = self.small_font.render(header_text, True, TEXT_COLOR)
            surface.blit(header, (40, 116))
            for index in range(3):
                rect = self.level_save_local_slot_rect(index)
                current_slot_locked = self.current_slot_locked(index)
                selected = index == self.save_slot_index
                if current_slot_locked:
                    fill = (11, 40, 50, 168)
                    edge = (88, 122, 132)
                else:
                    fill = (27, 92, 110, 220) if selected else (17, 63, 82, 200)
                    edge = (208, 246, 255) if selected else (96, 148, 160)
                pygame.draw.rect(surface, fill, rect, border_radius=10)
                pygame.draw.rect(surface, edge, rect, 2, border_radius=10)
                slot_name, level_name, seed_total = self.load_slot_summary(index)
                prefix_text = f"存档 {index + 1}: "
                suffix_text = f" | {self.display_level_name(level_name)} | 种子 {seed_total}"
                prefix_surface = self.small_font.render(prefix_text, True, WHITE if not current_slot_locked else MUTED_TEXT)
                surface.blit(prefix_surface, prefix_surface.get_rect(midleft=(rect.left + 12, rect.centery)))
                name_x = rect.left + 12 + prefix_surface.get_width()
                if selected and self.save_editing:
                    cursor_visible = int(self.save_cursor_timer * 2) % 2 == 0
                    display_name = self.save_name_input
                    name_surface = self.small_font.render(display_name, True, WHITE)
                    surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))
                    cursor_surface = self.small_font.render("_", True, WHITE if cursor_visible else fill)
                    cursor_x = name_x + name_surface.get_width()
                    surface.blit(cursor_surface, cursor_surface.get_rect(midleft=(cursor_x, rect.centery - 2)))
                else:
                    name_surface = self.small_font.render(slot_name, True, WHITE if not current_slot_locked else MUTED_TEXT)
                    surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))
                suffix_surface = self.small_font.render(suffix_text, True, WHITE if not current_slot_locked else MUTED_TEXT)
                suffix_x = rect.right - 12 - suffix_surface.get_width()
                surface.blit(suffix_surface, suffix_surface.get_rect(midleft=(suffix_x, rect.centery)))

            current_name = self.save_name_input if self.save_name_input else self.default_save_name(self.save_slot_index)
            name_label = self.small_font.render(f"存档名：{current_name}", True, WHITE)
            hint = self.small_font.render("Esc 返回", True, MUTED_TEXT)
            surface.blit(name_label, (40, 322))
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 352)))

        if self.save_message:
            message_surface = self.small_font.render(self.save_message, True, (255, 221, 126))
            surface.blit(message_surface, message_surface.get_rect(center=(panel.width / 2, panel.height - 18)))

        screen.blit(surface, panel.topleft)

    def big_level_save_font(self):
        return self.make_font(34)

    def draw_confirm_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 170))
        screen.blit(overlay, (0, 0))

        panel = CONFIRM_PANEL
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)

        title = self.tab_font.render("进度未保存", True, WHITE)
        body_text = (
            "当前进度尚未保存。继续前要保存吗？"
            if self.confirm_save_available()
            else self.confirm_message
        )
        body = self.small_font.render(body_text, True, TEXT_COLOR)
        hint_text = "左右进行选择，回车确认，Esc取消" if self.confirm_save_available() else "回车继续，Esc取消"
        hint = self.small_font.render(hint_text, True, MUTED_TEXT)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 46)))
        surface.blit(body, body.get_rect(center=(panel.width / 2, 96)))
        surface.blit(hint, hint.get_rect(center=(panel.width / 2, 128)))

        if self.confirm_save_available():
            self.draw_confirm_button(surface, self.confirm_local_no_rect(), "不保存", self.confirm_selected == "no")
            self.draw_confirm_button(surface, self.confirm_local_yes_rect(), "保存", self.confirm_selected == "yes")
        else:
            self.draw_confirm_button(surface, self.confirm_local_no_rect(), "取消", False)
            self.draw_confirm_button(surface, self.confirm_local_yes_rect(), "继续", True)
        self.draw_confirm_close_button(surface)
        screen.blit(surface, panel.topleft)

    def draw_confirm_close_button(self, surface):
        rect = self.confirm_local_close_rect()
        pygame.draw.circle(surface, (208, 246, 255), rect.center, 11, 2)
        text = self.small_font.render("x", True, TEXT_COLOR)
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery - 1)))

    def draw_confirm_button(self, surface, rect, label, selected):
        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(button, button.get_rect(), selected=selected, radius=10)
        text = self.small_font.render(label, True, WHITE if selected else TEXT_COLOR)
        button.blit(text, text.get_rect(center=button.get_rect().center))
        surface.blit(button, rect)

    def level_save_action_rect(self, index):
        rect = self.level_save_local_action_rect(index)
        return rect.move(LEVEL_SAVE_PANEL.left, LEVEL_SAVE_PANEL.top)

    def level_save_slot_rect(self, index):
        rect = self.level_save_local_slot_rect(index)
        return rect.move(LEVEL_SAVE_PANEL.left, LEVEL_SAVE_PANEL.top)

    def level_save_local_action_rect(self, index):
        return pygame.Rect(72, 164 + index * 60, LEVEL_SAVE_PANEL.width - 144, 42)

    def level_save_local_slot_rect(self, index):
        return pygame.Rect(40, 154 + index * 48, LEVEL_SAVE_PANEL.width - 80, 38)

    def confirm_no_rect(self):
        return self.confirm_local_no_rect().move(CONFIRM_PANEL.left, CONFIRM_PANEL.top)

    def confirm_save_rect(self):
        return self.confirm_yes_rect()

    def confirm_yes_rect(self):
        return self.confirm_local_yes_rect().move(CONFIRM_PANEL.left, CONFIRM_PANEL.top)

    def confirm_close_rect(self):
        return self.confirm_local_close_rect().move(CONFIRM_PANEL.left, CONFIRM_PANEL.top)

    def confirm_local_no_rect(self):
        if self.confirm_save_available():
            return pygame.Rect(110, 154, 144, 38)
        return pygame.Rect(110, 154, 144, 38)

    def confirm_local_save_rect(self):
        return self.confirm_local_yes_rect()

    def confirm_local_yes_rect(self):
        if self.confirm_save_available():
            return pygame.Rect(326, 154, 144, 38)
        return pygame.Rect(326, 154, 144, 38)

    def confirm_local_close_rect(self):
        return pygame.Rect(CONFIRM_PANEL.width - 42, 22, 24, 24)

    def draw_settings(self, screen):
        self.draw_back_button(screen)
        heading = self.subtitle_font.render("设置", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 190)))

        for index, (label, value) in enumerate(self.settings_rows()):
            rect = self.setting_rect(index)
            selected = index == self.settings_index
            self.draw_glass_panel(screen, rect, selected=selected)
            color = WHITE if selected else TEXT_COLOR
            label_surface = self.settings_font.render(label, True, color)
            value_surface = self.small_font.render(value, True, color)
            screen.blit(label_surface, label_surface.get_rect(midleft=(rect.left + 18, rect.centery)))
            screen.blit(value_surface, value_surface.get_rect(midright=(rect.right - 18, rect.centery)))

        hint = self.small_font.render("上下选择，左右调整", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def settings_rows(self):
        return [
            ("音乐", f"{self.music_volume}%"),
            ("音效", f"{self.sfx_volume}%"),
            ("重开时显示提示动画", "开" if self.restart_hint_enabled else "关"),
        ]

    def settings_count(self):
        return len(self.settings_rows())

    def setting_rect(self, index):
        return pygame.Rect(SCREEN_WIDTH / 2 - 210, 236 + index * 58, 420, 46)

    def setting_at_pos(self, pos):
        for index in range(self.settings_count()):
            if self.setting_rect(index).collidepoint(pos):
                return index
        return None

    def draw_back_button(self, screen):
        rect = pygame.Rect(44, 38, 116, 42)
        self.draw_glass_panel(screen, rect, selected=False)
        label = self.small_font.render("返回", True, TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_glass_tab(self, screen, rect, label, selected):
        self.draw_glass_panel(screen, rect, selected)
        if selected:
            pygame.draw.circle(screen, ENERGY_COLOR, (rect.left + 28, rect.centery), 5)
        text = self.tab_font.render(label, True, WHITE if selected else TEXT_COLOR)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_glass_panel(self, screen, rect, selected):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(surface, surface.get_rect(), selected)
        screen.blit(surface, rect)

    def draw_liquid_glass_surface(self, surface, rect, selected, radius=8):
        shadow = rect.move(0, 5)
        pygame.draw.rect(surface, (0, 0, 0, 36), shadow, border_radius=radius)

        fill_alpha = 28 if selected else 17
        edge_alpha = 218 if selected else 142
        pygame.draw.rect(surface, (255, 255, 255, fill_alpha), rect, border_radius=radius)
        pygame.draw.rect(surface, (255, 255, 255, edge_alpha), rect, 2, border_radius=radius)
        pygame.draw.rect(surface, (255, 255, 255, 38), rect.inflate(-8, -8), 1, border_radius=max(4, radius - 2))

        highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(
            highlight,
            (255, 255, 255, 44 if selected else 28),
            (-rect.width * 0.2, -rect.height * 0.55, rect.width * 0.9, rect.height * 0.8),
        )
        pygame.draw.arc(
            highlight,
            (255, 255, 255, 86 if selected else 48),
            (12, 8, rect.width - 24, max(18, rect.height // 2)),
            math.radians(188),
            math.radians(350),
            2,
        )
        pygame.draw.arc(
            highlight,
            (255, 255, 255, 30),
            (rect.width // 2, rect.height // 3, rect.width // 2, rect.height // 2),
            math.radians(100),
            math.radians(235),
            2,
        )
        surface.blit(highlight, rect.topleft)

        if selected:
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 255, 255, 40), glow.get_rect().inflate(-10, -10), border_radius=max(4, radius - 2))
            pygame.draw.line(glow, (255, 255, 255, 82), (18, 10), (rect.width - 18, 10), 2)
            pygame.draw.line(glow, (*GOAL_COLOR, 70), (18, rect.height - 9), (rect.width - 18, rect.height - 9), 2)
            surface.blit(glow, rect.topleft)

    def current_tab_rects(self):
        if self.mode == "levels":
            return [self.level_tab_rect(index) for index in range(len(self.visible_level_indices))]
        if self.mode == "main":
            return [self.main_tab_rect(index) for index in range(len(self.main_tabs))]
        return []

    def main_tab_rect(self, index):
        width = 340
        height = 54
        gap = 12
        top = 166
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)

    def level_tab_rect(self, index):
        width = 300
        height = 54
        gap = 16
        top = 220
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)

    def level_save_rect(self):
        return pygame.Rect(44, 38, 116, 42)

    def can_attempt_region_unlock(self):
        return self.progress_data.get("player_seeds", 0) >= self.unlock_seed_cost

    def default_save_name(self, slot_index):
        return f"存档 {slot_index + 1}"

    def slot_display_name(self, slot_index):
        if slot_index is None:
            return self.default_save_name(0)
        slot = self.save_manager.get_slot(slot_index) if self.save_manager else None
        if slot and slot.get("name"):
            return slot["name"]
        return self.default_save_name(slot_index)

    def begin_level_save(self, return_mode="levels", base_mode="levels", continue_after_save=False):
        self.mode = "level_save"
        self.level_save_return_mode = return_mode
        self.level_save_base_mode = base_mode
        self.level_save_continue_after_save = continue_after_save
        self.save_message = ""
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.save_action_index = 0
        self.save_forbid_current_slot = self.progress_data.get("slot_index") is not None
        if self.progress_data.get("slot_index") is None:
            self.save_flow = "choose_slot"
            self.save_slot_index = 0
        else:
            self.save_flow = "choose_action"
            self.save_slot_index = self.progress_data.get("slot_index")
        self.save_name_input = self.slot_display_name(self.save_slot_index)

    def close_level_save(self, show_message=False, saved=False):
        if not show_message:
            self.save_message = ""
        self.save_editing = False
        self.mode = self.level_save_return_mode
        if saved and self.mode == "confirm" and self.level_save_continue_after_save:
            self.level_save_continue_after_save = False
            return self.confirm_pending_action()
        if saved and self.mode == "confirm":
            self.confirm_message = "进度已保存。继续吗？"
        self.level_save_continue_after_save = False
        return None

    def save_action_options(self):
        if self.progress_data.get("slot_index") is None:
            return [("另存为新存档", "save_as_new")]
        return [
            ("覆盖当前存档", "update_current"),
            ("另存为新存档", "save_as_new"),
        ]

    def move_save_slot_selection(self, delta):
        available_slots = [0, 1, 2]
        current_slot_index = self.progress_data.get("slot_index")
        if self.save_forbid_current_slot and current_slot_index is not None:
            available_slots = [index for index in available_slots if index != current_slot_index]
        if not available_slots:
            return
        current = self.save_slot_index if self.save_slot_index in available_slots else available_slots[0]
        index = available_slots.index(current)
        self.save_slot_index = available_slots[(index + delta) % len(available_slots)]
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

    def begin_save_name_edit(self):
        self.save_editing = True
        self.save_name_input = ""
        self.save_message = "输入名称后，再按回车保存"
        self.save_cursor_timer = 0.0

    def build_save_snapshot(self, name):
        current_level_index = self.progress_data.get("current_level_index", 0)
        latest_level_index = self.progress_data.get("latest_level_index", current_level_index)
        latest_level_name = self.all_level_tabs[min(latest_level_index, len(self.all_level_tabs) - 1)][0]
        return {
            "name": name.strip() or self.default_save_name(self.save_slot_index),
            "current_level_index": current_level_index,
            "latest_level_index": latest_level_index,
            "latest_level_name": latest_level_name,
            "unlocked_levels": self.progress_data.get("unlocked_levels", 0),
            "player_bubbles": self.progress_data.get("player_bubbles", 1),
            "player_seeds": self.progress_data.get("player_seeds", 0),
            "seed_total": self.progress_data.get("seed_total", self.progress_data.get("player_seeds", 0)),
            "completed_level_states": self.progress_data.get("completed_level_states", {}),
            "stars_by_level": self.progress_data.get("stars_by_level", {}),
            "current_region": self.progress_data.get("current_region", "nursery"),
            "thorn_reef_unlocked": self.progress_data.get("thorn_reef_unlocked", False),
            "restart_hint_enabled": self.restart_hint_enabled,
        }

    def save_to_slot(self, slot_index):
        if not self.save_manager:
            self.save_message = "存档系统不可用"
            return False
        if slot_index is None:
            self.save_message = "请选择有效存档位"
            return False
        if (
            self.save_flow == "choose_slot"
            and self.save_forbid_current_slot
            and self.progress_data.get("slot_index") is not None
            and slot_index == self.progress_data.get("slot_index")
        ):
            self.save_message = "请选择另一个存档位"
            return False
        snapshot = self.build_save_snapshot(self.save_name_input)
        self.save_manager.save_slot(slot_index, snapshot)
        self.progress_data = dict(self.progress_data)
        self.progress_data["slot_index"] = slot_index
        self.progress_data["latest_level_name"] = snapshot["latest_level_name"]
        self.progress_data["restart_hint_enabled"] = self.restart_hint_enabled
        self.save_message = f"已保存到存档 {slot_index + 1}"
        self.save_name_input = snapshot["name"]
        if self.progress_data.get("has_started_game"):
            self.session_progress = dict(self.progress_data)
        self.session_dirty = False
        return True

    def mark_progress_dirty(self):
        self.progress_data["has_started_game"] = True
        self.session_progress = dict(self.progress_data)
        self.session_dirty = True

    def request_window_close_action(self):
        return self.request_quit_action()

    def session_progress_state(self):
        if self.progress_data.get("has_started_game"):
            return self.progress_data
        return None


    def begin_region_unlock(self):
        self.unlock_confirmation = (
            f"消耗 {self.unlock_seed_cost} 颗种子解锁荆棘礁？"
            if self.can_attempt_region_unlock()
            else f"需要 {self.unlock_seed_cost} 颗种子才能解锁荆棘礁"
        )
        self.mode = "unlock_confirm"
        return None

    def start_region_unlock(self):
        if not self.can_attempt_region_unlock():
            self.unlock_status_message = f"还需要先收集 {self.unlock_seed_cost} 颗种子"
            self.mode = "unlock_result"
            self.unlock_failed = False
            return
        player_pos = (120, 150)
        self.unlock_player = Player(player_pos)
        self.unlock_player.bubble_count = self.progress_data.get("player_bubbles", 1)
        self.unlock_player.seed_count = self.progress_data.get("player_seeds", 0)
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = self.unlock_animation_interval
        self.unlock_failed = False
        self.mode = "unlock_anim"

    def update_region_unlock(self, dt):
        self.unlock_timer -= dt
        if self.unlock_timer > 0:
            return
        self.unlock_timer += self.unlock_animation_interval
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()
            return
        if self.unlock_player.bubble_count <= 1 or self.unlock_player.seed_count <= 0:
            self.unlock_player.bubble_count = 0
            self.unlock_failed = True
            self.unlock_status_message = "泡泡破裂。返回初生海 - 1。"
            self.mode = "unlock_result"
            return
        self.unlock_player.bubble_count -= 1
        self.unlock_player.seed_count -= 1
        emitted = WildSeed(
            250 + self.unlock_emit_count * 62,
            152,
        )
        self.unlock_emitted.append(emitted)
        self.unlock_emit_count += 1
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()

    def finish_region_unlock(self):
        self.progress_data["player_bubbles"] = self.unlock_player.bubble_count
        self.progress_data["player_seeds"] = self.unlock_player.seed_count
        self.progress_data["seed_total"] = self.unlock_player.seed_count
        self.progress_data["thorn_reef_unlocked"] = True
        self.progress_data["current_region"] = "thorn_reef"
        self.progress_data["viewed_region"] = "thorn_reef"
        self.progress_data["current_level_index"] = 4
        self.progress_data["latest_level_index"] = max(self.progress_data.get("latest_level_index", 0), 4)
        self.progress_data["unlocked_levels"] = max(self.progress_data.get("unlocked_levels", 0), 4)
        self.thorn_reef_unlocked = True
        self.current_region = "thorn_reef"
        self.refresh_progress_state()
        self.level_selected = 4
        self.map_message = "荆棘礁已解锁"
        self.mode = "levels"
        self.mark_progress_dirty()

    def reset_to_nursery_start(self):
        slot_index = self.progress_data.get("slot_index")
        self.progress_data = self.default_progress_data()
        if slot_index is not None:
            self.progress_data["slot_index"] = slot_index
        self.refresh_progress_state()
        self.level_selected = 0
        self.map_message = "泡泡破裂。请从初生海重新开始。"
        self.mark_progress_dirty()

    def draw_unlock_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 180))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(170, 132, 620, 280)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)
        title = self.tab_font.render("解锁荆棘礁", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 40)))
        if self.mode == "unlock_confirm":
            body = self.subtitle_font.render(self.unlock_confirmation, True, TEXT_COLOR)
            surface.blit(body, body.get_rect(center=(panel.width / 2, 112)))
            hint = self.small_font.render("回车确认，Esc 取消", True, MUTED_TEXT)
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 240)))
        else:
            if self.unlock_player:
                self.unlock_player.draw(surface)
            for seed in self.unlock_emitted:
                clone = WildSeed(seed.x, seed.y)
                clone.draw(surface)
            if self.mode == "unlock_anim":
                hint = self.small_font.render("正在献出 4 颗种子泡泡，穿越礁门……", True, TEXT_COLOR)
            else:
                hint = self.small_font.render(self.unlock_status_message, True, (255, 221, 126))
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 238)))
        screen.blit(surface, panel.topleft)
