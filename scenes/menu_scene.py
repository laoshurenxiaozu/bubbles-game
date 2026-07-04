from pathlib import Path

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.fonts import brand_font, ui_font
from core.input import is_cancel, is_confirm, is_down, is_left, is_no, is_right, is_save, is_up, is_yes
from core.save_flow import SaveFlowMixin
from core.sounds import SoundManager
from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    first_level_index,
    level_indices_for_region,
    level_internal_name,
    level_tabs,
    region_display_name,
)
from ui.level_map import LevelMapView
from ui.menu_effects import (
    bubble_position_at_time as animated_bubble_position,
    default_menu_bubbles,
)
from entities.objects import BurstEffect, WildSeed
from entities.player import Player
from scenes.level_scene import LevelScene
from ui.dialogs import ConfirmationDialogView, SaveDialogView
from ui.menu_view import MenuView
from ui.region_unlock import RegionUnlockView


BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "underwater_menu_bg.png"


class MenuScene(SaveFlowMixin):
    def __init__(
        self,
        save_manager=None,
        progress_data=None,
        session_progress=None,
        session_dirty=False,
        sfx_volume=80,
        music_volume=80,
    ):
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
        self.confirm_dialog_view = ConfirmationDialogView(self)
        self.save_dialog_view = SaveDialogView(self)
        self.menu_view = MenuView(self)
        self.region_unlock_view = RegionUnlockView(self)
        self.mode = self.progress_data.get("open_mode", "main")
        self.selected = 0
        self.settings_index = 0
        self.level_selected = 0
        self.load_selected = 0
        self.level_hovered = None
        self.load_message = self.progress_data.get("load_message", "")
        self.map_message = self.progress_data.get("map_message", "")
        self.time = 0.0
        self.music_volume = music_volume
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
        self.all_level_tabs = level_tabs()
        self.unlock_seed_cost = 4
        self.unlock_animation_interval = 0.45
        self.unlock_confirmation = ""
        self.unlock_status_message = ""
        self.unlock_player = None
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = 0.0
        self.unlock_failed = False
        self.unlock_burst_effect = None
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
        self.level_preview_scene = None
        self.level_preview_index = None
        self.level_map_view = LevelMapView(self)
        self.refresh_progress_state()

    def make_font(self, size):
        return ui_font(size)

    def load_background_image(self):
        if not BACKGROUND_PATH.exists():
            return None
        try:
            image = pygame.image.load(str(BACKGROUND_PATH))
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def refresh_progress_state(self):
        self.main_tabs = self.build_main_tabs()
        self.current_region = self.progress_data.get("current_region", DEFAULT_REGION)
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
        handler = {
            "main": self.handle_main_key,
            "levels": self.handle_level_map_key,
            "level_save": self.handle_level_save_key,
            "confirm": self.handle_confirm_key,
            "load": self.handle_load_key,
            "settings": self.handle_settings_key,
            "unlock_confirm": self.handle_unlock_confirm_key,
            "unlock_result": self.handle_unlock_result_key,
        }.get(self.mode)
        return handler(key) if handler else None

    def handle_main_key(self, key):
        if is_up(key):
            self.selected = (self.selected - 1) % len(self.main_tabs)
            self.sound.play("menu_move")
        elif is_down(key):
            self.selected = (self.selected + 1) % len(self.main_tabs)
            self.sound.play("menu_move")
        elif is_confirm(key):
            self.sound.play("menu_select")
            return self.activate_main_tab(self.selected)
        return None

    def handle_level_map_key(self, key):
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
        return None

    def handle_confirm_key(self, key):
        if is_cancel(key):
            self.cancel_confirmation()
            self.sound.play("menu_move")
        elif is_left(key) or is_right(key):
            self.move_confirmation_selection(
                -1 if is_left(key) else 1
            )
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
        return None

    def handle_load_key(self, key):
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
        return None

    def handle_settings_key(self, key):
        if is_cancel(key):
            self.mode = "main"
            self.sound.play("menu_select")
        elif is_up(key):
            self.settings_index = (
                self.settings_index - 1
            ) % self.settings_count()
            self.sound.play("menu_move")
        elif is_down(key):
            self.settings_index = (
                self.settings_index + 1
            ) % self.settings_count()
            self.sound.play("menu_move")
        elif is_left(key):
            self.adjust_setting(-10)
            self.sound.play("menu_move")
        elif is_right(key):
            self.adjust_setting(10)
            self.sound.play("menu_move")
        elif is_confirm(key) and self.settings_index == 2:
            self.sound.play("menu_select")
            self.toggle_restart_hint_setting()
        return None

    def adjust_setting(self, delta):
        if self.settings_index == 0:
            self.music_volume = max(
                0,
                min(100, self.music_volume + delta),
            )
        elif self.settings_index == 1:
            self.sfx_volume = max(
                0,
                min(100, self.sfx_volume + delta),
            )
            self.sound.set_sfx_volume(self.sfx_volume)
        else:
            self.toggle_restart_hint_setting()

    def handle_unlock_confirm_key(self, key):
        if is_cancel(key) or is_no(key):
            self.mode = "levels"
            self.unlock_confirmation = ""
            self.sound.play("menu_select")
        elif is_confirm(key) or is_yes(key):
            self.sound.play("menu_select")
            self.start_region_unlock()
        return None

    def handle_unlock_result_key(self, key):
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
        handlers = {
            "confirm": self.update_confirm_hover,
            "level_save": self.update_save_hover,
            "levels": self.update_level_map_hover,
            "load": self.update_load_hover,
            "settings": self.update_settings_hover,
        }
        handler = handlers.get(self.mode)
        if handler:
            handler(pos)
            return

        self.level_hovered = None
        for index, rect in enumerate(self.current_tab_rects()):
            if rect.collidepoint(pos):
                previous = self.selected
                self.selected = index
                self.play_menu_move_if_changed(
                    previous,
                    self.selected,
                )
                return

    def update_confirm_hover(self, pos):
        if not self.confirm_save_available():
            return
        previous = self.confirm_selected
        if self.confirm_yes_rect().collidepoint(pos):
            self.confirm_selected = "yes"
        elif self.confirm_no_rect().collidepoint(pos):
            self.confirm_selected = "no"
        self.play_menu_move_if_changed(
            previous,
            self.confirm_selected,
        )

    def update_save_hover(self, pos):
        if self.save_flow == "choose_action":
            for index, _ in enumerate(self.save_action_options()):
                if self.level_save_action_rect(index).collidepoint(pos):
                    previous = self.save_action_index
                    self.save_action_index = index
                    self.play_menu_move_if_changed(
                        previous,
                        self.save_action_index,
                    )
                    return
        else:
            for index in range(3):
                if self.level_save_slot_rect(index).collidepoint(pos):
                    if not self.current_slot_locked(index):
                        previous = self.save_slot_index
                        self.save_slot_index = index
                        self.play_menu_move_if_changed(
                            previous,
                            self.save_slot_index,
                        )
                    return

    def update_level_map_hover(self, pos):
        level_index = self.level_node_at_pos(pos)
        self.level_hovered = level_index
        if level_index == "gate":
            previous = self.level_selected
            self.level_selected = "gate"
            self.play_menu_move_if_changed(
                previous,
                self.level_selected,
            )
        elif (
            level_index is not None
            and self.is_level_unlocked(level_index)
        ):
            previous = self.level_selected
            self.level_selected = level_index
            self.play_menu_move_if_changed(
                previous,
                self.level_selected,
            )

    def update_load_hover(self, pos):
        self.level_hovered = None
        for index in range(3):
            if self.load_slot_rect(index).collidepoint(pos):
                previous = self.load_selected
                self.load_selected = index
                self.play_menu_move_if_changed(
                    previous,
                    self.load_selected,
                )
                return

    def update_settings_hover(self, pos):
        setting_index = self.setting_at_pos(pos)
        if setting_index is not None:
            previous = self.settings_index
            self.settings_index = setting_index
            self.play_menu_move_if_changed(
                previous,
                self.settings_index,
            )

    def handle_click(self, pos):
        handlers = {
            "confirm": self.handle_confirm_click,
            "level_save": self.handle_level_save_click,
            "levels": self.handle_level_map_click,
            "load": self.handle_load_click,
        }
        handler = handlers.get(self.mode)
        if handler:
            return handler(pos)

        for index, rect in enumerate(self.current_tab_rects()):
            if rect.collidepoint(pos):
                self.selected = index
                self.sound.play("menu_select")
                return self.activate_main_tab(index)

        if self.mode in ("settings", "unlock_confirm", "unlock_result"):
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

    def handle_confirm_click(self, pos):
        if self.confirm_close_rect().collidepoint(pos):
            self.cancel_confirmation()
            self.sound.play("menu_move")
            return None
        if self.confirm_save_available():
            if self.confirm_yes_rect().collidepoint(pos):
                self.confirm_selected = "yes"
                self.begin_confirmation_save()
                self.sound.play("menu_select")
            elif self.confirm_no_rect().collidepoint(pos):
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

    def handle_level_map_click(self, pos):
        hit = self.level_node_at_pos(pos)
        if hit == "gate":
            self.sound.play("menu_select")
            return self.begin_region_unlock()
        if hit is not None:
            self.sound.play("menu_select")
        return self.activate_level_node(hit)

    def handle_load_click(self, pos):
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
            "current_region": DEFAULT_REGION,
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
        return level_indices_for_region(self.viewed_region)

    @property
    def level_tabs(self):
        return self.visible_level_tabs()

    def visible_level_tabs(self):
        return [self.all_level_tabs[index] for index in self.visible_level_indices]

    def show_region_gate(self):
        return (
            self.viewed_region == DEFAULT_REGION
            and not self.thorn_reef_unlocked
            and self.all_region_levels_unlocked(DEFAULT_REGION)
        )

    def all_region_levels_unlocked(self, region):
        indices = level_indices_for_region(region)
        return bool(indices) and all(
            index <= self.latest_level_index
            for index in indices
        )

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
            if (
                self.viewed_region == THORN_REEF_REGION
                and self.level_selected == first_level_index(THORN_REEF_REGION)
            ):
                self.viewed_region = DEFAULT_REGION
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = self.visible_level_indices[-1]
                self.level_hovered = None
                self.map_message = region_display_name(DEFAULT_REGION)
                return True
            return False

        if self.viewed_region == DEFAULT_REGION:
            if self.thorn_reef_unlocked and self.level_selected == self.visible_level_indices[-1]:
                self.viewed_region = THORN_REEF_REGION
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = first_level_index(THORN_REEF_REGION)
                self.level_hovered = None
                self.map_message = region_display_name(THORN_REEF_REGION)
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
        if level_index is None:
            return None
        if not self.is_level_unlocked(level_index):
            if level_index in self.visible_level_indices:
                self.map_message = "新的枝芽，还未在这里绽放"
            return None
        if not self.is_level_playable(level_index):
            if level_index in self.visible_level_indices:
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
        return self.prepare_save_as_new()

    def current_slot_locked(self, slot_index):
        return self.is_save_slot_locked(slot_index)

    def select_level_save_slot(self, slot_index, begin_edit_on_repeat=False):
        return self.select_save_slot(
            slot_index,
            begin_edit_on_repeat,
        )

    def is_level_unlocked(self, level_index):
        return level_index in self.visible_level_indices and level_index <= self.latest_level_index

    def is_level_playable(self, level_index):
        if not self.is_level_unlocked(level_index):
            return False
        if (
            self.current_region == THORN_REEF_REGION
            and level_index in level_indices_for_region(DEFAULT_REGION)
        ):
            return False
        return True

    def level_node_centers(self):
        return self.level_map_view.node_centers()

    def level_node_at_pos(self, pos):
        return self.level_map_view.node_at_pos(pos)

    def update(self, dt):
        self.time += dt
        if self.mode == "levels":
            self.update_level_preview(dt)
        if self.mode == "unlock_anim":
            self.update_region_unlock(dt)
        elif self.mode == "unlock_burst":
            self.update_region_unlock_burst(dt)
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
        if self.mode in ("unlock_confirm", "unlock_anim", "unlock_burst", "unlock_result"):
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
        if self.level_save_base_mode in ("unlock_confirm", "unlock_anim", "unlock_burst", "unlock_result"):
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
        if self.confirm_return_mode in ("unlock_confirm", "unlock_anim", "unlock_burst", "unlock_result"):
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
        return self.menu_view.draw_background(screen)

    def bubble_position_at_time(self, bubble, elapsed):
        return animated_bubble_position(bubble, elapsed)

    def draw_title(self, screen):
        return self.menu_view.draw_title(screen)

    def draw_main(self, screen):
        return self.menu_view.draw_main(screen)

    def draw_levels(self, screen):
        self.level_map_view.draw(screen)

    def previewed_map_item(self):
        if self.level_hovered is not None:
            return self.level_hovered
        return self.level_selected

    def ensure_level_preview(self, level_index):
        if not isinstance(level_index, int):
            return None
        if (
            self.level_preview_scene is not None
            and self.level_preview_index == level_index
        ):
            return self.level_preview_scene
        self.level_preview_scene = LevelScene(
            level_index=level_index,
            save_manager=self.save_manager,
            slot_index=self.progress_data.get("slot_index"),
            save_data=self.progress_data,
            sfx_volume=self.sfx_volume,
            music_volume=self.music_volume,
        )
        self.level_preview_scene.start_world_without_player()
        self.level_preview_index = level_index
        return self.level_preview_scene

    def update_level_preview(self, dt):
        preview = self.ensure_level_preview(
            self.previewed_map_item()
        )
        if preview is not None:
            preview.update(dt)

    def draw_level_preview(self, surface, rect, level_index):
        preview = self.ensure_level_preview(level_index)
        if preview is None:
            return
        frame = preview.render_world_surface()
        scaled = pygame.transform.smoothscale(
            frame,
            rect.size,
        )
        surface.blit(scaled, rect)

    def draw_load(self, screen):
        return self.menu_view.draw_load(screen)

    def region_gate_center(self):
        return self.level_map_view.region_gate_center()

    def draw_region_gate(self, screen):
        return self.level_map_view.draw_region_gate(screen)

    def level_hover_panel_rect(self):
        return self.level_map_view.hover_panel_rect()

    def load_back_rect(self):
        return self.menu_view.load_back_rect()

    def load_slot_rect(self, index):
        return self.menu_view.load_slot_rect(index)

    def load_slot_summary(self, slot_index):
        return self.save_slot_summary(slot_index)

    def draw_level_save_overlay(self, screen):
        return self.save_dialog_view.draw(screen)

    def draw_confirm_overlay(self, screen):
        return self.confirm_dialog_view.draw(screen)

    def level_save_action_rect(self, index):
        return self.save_dialog_view.action_rect(index)

    def level_save_slot_rect(self, index):
        return self.save_dialog_view.slot_rect(index)

    def confirm_no_rect(self):
        return self.confirm_dialog_view.no_rect()

    def confirm_yes_rect(self):
        return self.confirm_dialog_view.yes_rect()

    def confirm_close_rect(self):
        return self.confirm_dialog_view.close_rect()

    def draw_settings(self, screen):
        return self.menu_view.draw_settings(screen)

    def settings_rows(self):
        return [
            ("音乐", f"{self.music_volume}%"),
            ("音效", f"{self.sfx_volume}%"),
            ("重开时显示提示动画", "开" if self.restart_hint_enabled else "关"),
        ]

    def settings_count(self):
        return len(self.settings_rows())

    def setting_rect(self, index):
        return self.menu_view.setting_rect(index)

    def setting_at_pos(self, pos):
        return self.menu_view.setting_at_pos(pos)

    def current_tab_rects(self):
        if self.mode == "main":
            return [self.main_tab_rect(index) for index in range(len(self.main_tabs))]
        return []

    def main_tab_rect(self, index):
        return self.menu_view.main_tab_rect(index)

    def can_attempt_region_unlock(self):
        return self.progress_data.get("player_seeds", 0) >= self.unlock_seed_cost

    def current_save_slot_index(self):
        return self.progress_data.get("slot_index")

    def begin_level_save(self, return_mode="levels", base_mode="levels", continue_after_save=False):
        self.mode = "level_save"
        self.level_save_return_mode = return_mode
        self.level_save_base_mode = base_mode
        self.level_save_continue_after_save = continue_after_save
        self.reset_save_flow()

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

    def build_save_snapshot(self, name):
        current_level_index = self.progress_data.get("current_level_index", 0)
        latest_level_index = self.progress_data.get("latest_level_index", current_level_index)
        latest_level_name = level_internal_name(
            min(latest_level_index, len(self.all_level_tabs) - 1)
        )
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
            "current_region": self.progress_data.get("current_region", DEFAULT_REGION),
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
            self.unlock_burst_effect = None
            return
        player_pos = (120, 150)
        self.unlock_player = Player(player_pos)
        self.unlock_player.bubble_count = self.progress_data.get("player_bubbles", 1)
        self.unlock_player.seed_count = self.progress_data.get("player_seeds", 0)
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = self.unlock_animation_interval
        self.unlock_failed = False
        self.unlock_burst_effect = None
        self.mode = "unlock_anim"

    def update_region_unlock(self, dt):
        self.unlock_timer -= dt
        if self.unlock_timer > 0:
            return
        self.unlock_timer += self.unlock_animation_interval
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()
            return
        if self.unlock_player.bubble_count <= 0 or self.unlock_player.seed_count <= 0:
            self.begin_region_unlock_failure()
            return
        burst_radius = self.unlock_player.radius
        self.unlock_player.bubble_count -= 1
        self.unlock_player.seed_count -= 1
        emitted = WildSeed(
            250 + self.unlock_emit_count * 62,
            152,
        )
        self.unlock_emitted.append(emitted)
        self.unlock_emit_count += 1
        self.sound.play("seed_release")
        if self.unlock_player.bubble_count <= 0:
            self.begin_region_unlock_failure(burst_radius)
            return
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()

    def begin_region_unlock_failure(self, burst_radius=None):
        self.unlock_player.bubble_count = 0
        self.unlock_player.burst = True
        self.unlock_failed = True
        self.unlock_status_message = "泡泡破裂。返回初生海 - 1。"
        self.unlock_burst_effect = BurstEffect(
            self.unlock_player.x,
            self.unlock_player.y,
            burst_radius or self.unlock_player.radius,
        )
        self.mode = "unlock_burst"
        self.sound.play("bubble_burst")

    def update_region_unlock_burst(self, dt):
        if self.unlock_burst_effect is None:
            self.mode = "unlock_result"
            return
        self.unlock_burst_effect.update(dt)
        if self.unlock_burst_effect.done:
            self.mode = "unlock_result"

    def finish_region_unlock(self):
        target_level_index = first_level_index(THORN_REEF_REGION)
        self.progress_data["player_bubbles"] = self.unlock_player.bubble_count
        self.progress_data["player_seeds"] = self.unlock_player.seed_count
        self.progress_data["seed_total"] = self.unlock_player.seed_count
        self.progress_data["thorn_reef_unlocked"] = True
        self.progress_data["current_region"] = THORN_REEF_REGION
        self.progress_data["viewed_region"] = THORN_REEF_REGION
        self.progress_data["current_level_index"] = target_level_index
        self.progress_data["latest_level_index"] = max(
            self.progress_data.get("latest_level_index", 0),
            target_level_index,
        )
        self.progress_data["unlocked_levels"] = max(
            self.progress_data.get("unlocked_levels", 0),
            target_level_index,
        )
        self.thorn_reef_unlocked = True
        self.current_region = THORN_REEF_REGION
        self.refresh_progress_state()
        self.level_selected = target_level_index
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
        return self.region_unlock_view.draw(screen)
