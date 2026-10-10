"""PeppyMeter 右键菜单与运行时皮肤控制回归测试。"""

from types import SimpleNamespace

import pygame
import pytest

import peppymeter as peppymeter_module
import vumeter as vumeter_module
from configfileparser import (
    FRAME_RATE,
    METER,
    METER_NAMES,
    RANDOM_METER_INTERVAL,
    METER_FOLDER,
    SCREEN_INFO,
    WIDTH,
    HEIGHT,
    USE_CACHE,
)
from contextmenu import MeterContextMenu
from vumeter import Vumeter


RESOLUTIONS = [
    ("1280x400", "1280x400"),
    ("320x240", "320x240"),
    ("480x320", "480x320"),
    ("800x480", "800x480"),
]


def make_vumeter(meter_name="bar", names=None):
    names = names or ["bar", "blue", "red"]
    config = {
        METER: meter_name,
        METER_NAMES: names,
        RANDOM_METER_INTERVAL: 20,
        FRAME_RATE: 30,
        USE_CACHE: True,
    }
    meter = Vumeter(SimpleNamespace(meter_config=config), None)
    meter.current_meter_name = "bar"

    def fake_restart():
        if meter.forced_meter_name is not None:
            meter.util.meter_config[METER] = meter.forced_meter_name
            meter.current_meter_name = meter.forced_meter_name
            meter.forced_meter_name = None

    meter.restart = fake_restart
    return meter


def click(position):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position)


def test_menu_clamps_to_window_and_opens_resolution_submenu():
    menu = MeterContextMenu(RESOLUTIONS)
    menu.open_at((630, 470), (640, 480))

    assert menu.rect.right <= 640
    assert menu.rect.bottom <= 480
    action = menu.handle_event(click((menu.rect.centerx, menu.rect.top + menu.row_height // 2)))

    assert action is None
    assert menu.submenu_open
    assert menu.submenu_rect.right <= 640
    assert menu.submenu_rect.bottom <= 480


def test_menu_selects_resolution_and_returns_main_actions():
    menu = MeterContextMenu(RESOLUTIONS)
    for row, (_, folder) in enumerate(RESOLUTIONS):
        menu.open_at((20, 20), (640, 480))
        menu.handle_event(click((menu.rect.centerx, menu.rect.top + menu.row_height // 2)))
        position = (
            menu.submenu_rect.centerx,
            menu.submenu_rect.top + row * menu.SUBMENU_ROW_HEIGHT + menu.SUBMENU_ROW_HEIGHT // 2,
        )
        assert menu.handle_event(click(position)) == ("resolution", folder)
        assert not menu.is_open

    menu.open_at((20, 20), (640, 480))
    for row, expected in ((1, "random_now"), (2, "toggle_timed"), (3, "previous"), (4, "next")):
        menu.open_at((20, 20), (640, 480))
        position = (menu.rect.centerx, menu.rect.top + row * menu.row_height + menu.row_height // 2)
        assert menu.handle_event(click(position)) == expected


def test_menu_closes_on_outside_click():
    menu = MeterContextMenu(RESOLUTIONS)
    menu.open_at((20, 20), (640, 480))

    assert menu.handle_event(click((500, 400))) is None
    assert not menu.is_open


def test_menu_draws_on_a_pygame_surface():
    menu = MeterContextMenu(RESOLUTIONS)
    menu.open_at((20, 20), (320, 240))
    menu.handle_event(click((menu.rect.centerx, menu.rect.top + menu.row_height // 2)))
    surface = pygame.Surface((320, 240))

    menu.draw(surface, timed_random_enabled=True, current_resolution="480 × 320")


def test_manual_skin_changes_wrap_and_disable_timed_random():
    meter = make_vumeter()
    meter.set_timed_random_enabled(True)

    meter.next_manual_meter()
    assert meter.util.meter_config[METER] == "blue"
    assert not meter.timed_random_enabled

    meter.previous_manual_meter()
    assert meter.util.meter_config[METER] == "bar"
    meter.previous_manual_meter()
    assert meter.util.meter_config[METER] == "red"


def test_immediate_random_switch_preserves_timed_mode(monkeypatch):
    meter = make_vumeter()
    meter.set_timed_random_enabled(True)
    meter.random_meter_names = ["blue", "red"]
    monkeypatch.setattr(vumeter_module, "randrange", lambda *args: 0)

    meter.switch_to_random_meter()

    assert meter.util.meter_config[METER] == "blue"
    assert meter.timed_random_enabled


@pytest.mark.parametrize(
    ("folder", "size", "count"),
    [("1280x400", (1280, 400), 8), ("320x240", (320, 240), 25),
     ("480x320", (480, 320), 25), ("800x480", (800, 480), 25)],
)
def test_parser_loads_each_resolution(folder, size, count):
    from configfileparser import ConfigFileParser, HEIGHT, SCREEN_INFO, WIDTH

    config = ConfigFileParser(meter_folder=folder).meter_config

    assert (config[SCREEN_INFO][WIDTH], config[SCREEN_INFO][HEIGHT]) == size
    assert config[METER_NAMES] and len(config[METER_NAMES]) == count


def test_resolution_change_reuses_the_existing_audio_source(monkeypatch):
    from configfileparser import ConfigFileParser

    old_config = ConfigFileParser().meter_config
    audio_source = object()
    old_meter = SimpleNamespace(
        current_meter_name=old_config[METER],
        timed_random_enabled=True,
        stopped=False,
        stop=lambda: None,
        start=lambda: None,
    )
    new_meters = []

    class FakeMeter:
        def __init__(self, source):
            self.data_source = source
            self.timed_random_enabled = False

        def set_timed_random_enabled(self, enabled):
            self.timed_random_enabled = enabled

        def start(self):
            pass

    app = SimpleNamespace(
        util=SimpleNamespace(meter_config=old_config),
        meter=old_meter,
        data_source=audio_source,
        current_image=None,
        update_period=1,
        set_display_mode=lambda: None,
        output_display=lambda source: new_meters.append(FakeMeter(source)) or new_meters[-1],
    )
    monkeypatch.setattr(peppymeter_module.pygame.display, "update", lambda *args: None)

    assert peppymeter_module.Peppymeter.change_resolution(app, "320x240")
    assert app.util.meter_config[SCREEN_INFO][WIDTH] == 320
    assert app.util.meter_config[SCREEN_INFO][HEIGHT] == 240
    assert new_meters[0].data_source is audio_source
    assert new_meters[0].timed_random_enabled


def test_arrow_shortcuts_cycle_resolutions_and_skin_direction():
    resolutions = []
    skin_actions = []

    class FakeMenu:
        def __init__(self):
            self.is_open = True

        def close(self):
            self.is_open = False

    app = SimpleNamespace(
        util=SimpleNamespace(meter_config={SCREEN_INFO: {METER_FOLDER: "320x240"}}),
        meter=SimpleNamespace(
            previous_manual_meter=lambda: skin_actions.append("previous"),
            next_manual_meter=lambda: skin_actions.append("next"),
        ),
        context_menu=FakeMenu(),
    )

    def change_resolution(folder):
        resolutions.append(folder)
        app.util.meter_config[SCREEN_INFO][METER_FOLDER] = folder
        return True

    app.change_resolution = change_resolution

    assert peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_UP)
    assert not app.context_menu.is_open
    assert peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_DOWN)
    app.context_menu.is_open = True
    assert peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_LEFT)
    assert not app.context_menu.is_open
    app.context_menu.is_open = True
    assert peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_RIGHT)
    assert not app.context_menu.is_open
    assert not peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_ESCAPE)

    assert resolutions == ["480x320", "320x240"]
    assert skin_actions == ["previous", "next"]


def test_up_shortcut_wraps_to_first_resolution():
    resolutions = []
    app = SimpleNamespace(
        util=SimpleNamespace(meter_config={SCREEN_INFO: {METER_FOLDER: "1280x400"}}),
        meter=SimpleNamespace(),
        context_menu=SimpleNamespace(is_open=False),
        change_resolution=lambda folder: resolutions.append(folder) or True,
    )

    assert peppymeter_module.Peppymeter.handle_shortcut_key(app, pygame.K_UP)
    assert resolutions == ["320x240"]
