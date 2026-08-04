"""Widgets for the Dynamic Pine hub's "Dynamic Pine" tab: one group of
controls per installed game, plus the shared BIOS row. Kept out of context.py
since it's pure kvui/kivymd layout code with no CommonContext concerns of its
own - context.py just calls build_game_group/build_bios_row per game."""
from __future__ import annotations

from typing import Callable

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kvui import MDLabel

from Utils import open_filename

from .api import DynamicPineGame, get_bios_path, get_iso_path
from .launcher import list_instances, prompt_for_bios, prompt_for_iso


def _build_iso_row(game_name: str, spec: DynamicPineGame) -> MDBoxLayout:
    """Status label, plus a locate button while the game's ISO isn't detected -
    choosing one persists to host.yaml and the button disappears."""
    row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
    iso = get_iso_path(spec)
    iso_detected = iso is not None and iso.exists()
    label = MDLabel(
        text=f"ISO: {iso}" if iso_detected else
             (f"ISO: configured but not found at {iso}" if iso else "ISO: not found"),
        shorten=True, shorten_from="left")
    row.add_widget(label)

    if not iso_detected:
        locate_button = MDButton(MDButtonText(text="Locate ISO..."))

        def on_locate(_btn):
            chosen = prompt_for_iso(game_name, spec)
            if chosen is not None:
                label.text = f"ISO: {chosen}"
                row.remove_widget(locate_button)

        locate_button.bind(on_release=on_locate)
        row.add_widget(locate_button)
    return row


def _build_instances_label(spec: DynamicPineGame) -> tuple[MDLabel, Callable[[], None]]:
    """A label that lists this game's PCSX2 instances and their running
    status, refreshing itself every few seconds so a client started outside
    the hub still shows up as "running" shortly after - plus the refresh
    callback itself, so launch/clear button handlers can force an immediate
    update instead of waiting for the next tick."""
    label = MDLabel(text="Instances: checking...", size_hint_y=None, height=dp(24))

    def refresh(_dt=None) -> None:
        try:
            instances = list_instances(spec)
        except Exception as exc:
            label.text = f"Instances: unavailable ({exc})"
            return
        label.text = ("Instances: " + ", ".join(
            f"{i.instance_id} (port {i.port}, {'running' if i.running else 'stopped'})"
            for i in instances)) if instances else "Instances: none created yet"

    Clock.schedule_interval(refresh, 3)
    refresh()
    return label, refresh


def _build_launch_controls(game_name: str, spec: DynamicPineGame,
                           instance_field: MDTextField, on_refresh) -> MDBoxLayout:
    """The row of action buttons: one combined "Launch" button ('simple'
    launcher_options), separate "Launch PCSX2"/"Launch Client" buttons
    ('full', the default), just "Launch Client" and nothing PCSX2-related
    ('client', for games whose client launches PCSX2 itself), or a
    "Patch & Launch" button that prompts for a patch_file_suffix file first
    ('patch', same as 'client' plus that per-launch file) - plus "Clear
    Unused" in every case."""
    from .context import _LAUNCH_ERRORS, launch_game_client, launch_simple
    from .launcher import launch_pcsx2, clear_unused_instances
    from CommonClient import logger

    controls = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(56))
    controls.add_widget(instance_field)

    def instance() -> str | None:
        return instance_field.text or None

    def on_launch_pcsx2(_btn) -> None:
        try:
            launch_pcsx2(game_name, instance())
        except _LAUNCH_ERRORS as exc:
            logger.warning(f"[DynamicPine] {exc}")
        on_refresh()

    def on_launch_simple(_btn) -> None:
        launch_simple(spec, game_name, instance())
        on_refresh()

    def on_launch_client(_btn) -> None:
        launch_game_client(spec, game_name, instance())

    def on_patch_and_launch(_btn) -> None:
        suffix = spec.patch_file_suffix
        filetypes = ((f"{game_name} patch", (suffix,)), ("All files", ("*",))) if suffix \
            else (("All files", ("*",)),)
        try:
            chosen = open_filename(f"Locate patch file for {game_name}", filetypes)
        except Exception as exc:
            logger.warning(f"[DynamicPine] Could not open a file dialog to locate the "
                           f"{game_name} patch file: {exc}")
            return
        if chosen:
            launch_game_client(spec, game_name, instance(), chosen)

    def on_clear_unused(_btn) -> None:
        removed = clear_unused_instances(spec)
        logger.info(f"[DynamicPine] Removed {len(removed)} unused instance(s) for {game_name}: "
                   f"{', '.join(removed) if removed else '(none)'}")
        on_refresh()

    if spec.launcher_options == "simple" and spec.client_component:
        # One button: launches PCSX2 with this game's configured settings and
        # starts the client together, marking the spawned client so it
        # doesn't redundantly launch PCSX2 again itself (see launch_simple's
        # docstring).
        launch_button = MDButton(MDButtonText(text="Launch"))
        launch_button.bind(on_release=on_launch_simple)
        controls.add_widget(launch_button)
    elif spec.launcher_options == "patch" and spec.client_component:
        # Like "client" below, but this game's client also needs a per-seed
        # patch file path before it can patch-and-launch itself - prompt for
        # one and forward it, the same way double-clicking that file would.
        patch_button = MDButton(MDButtonText(text="Patch & Launch"))
        patch_button.bind(on_release=on_patch_and_launch)
        controls.add_widget(patch_button)
    elif spec.launcher_options == "client" and spec.client_component:
        # Nothing PCSX2-related here at all - this game's client launches
        # PCSX2 itself (typically via launch_pcsx2 directly, e.g. once it's
        # finished patching a per-seed ISO), so the hub only starts it.
        client_button = MDButton(MDButtonText(text="Launch Client"))
        client_button.bind(on_release=on_launch_client)
        controls.add_widget(client_button)
    else:
        pcsx2_button = MDButton(MDButtonText(text="Launch PCSX2"))
        pcsx2_button.bind(on_release=on_launch_pcsx2)
        controls.add_widget(pcsx2_button)

        if spec.client_component:
            client_button = MDButton(MDButtonText(text="Launch Client"))
            client_button.bind(on_release=on_launch_client)
            controls.add_widget(client_button)

    clear_button = MDButton(MDButtonText(text="Clear Unused"))
    clear_button.bind(on_release=on_clear_unused)
    controls.add_widget(clear_button)
    return controls


def build_game_group(game_name: str, spec: DynamicPineGame) -> MDBoxLayout:
    """One game's whole control block: header, ISO row, instance/launch
    controls, and a live instances status label."""
    group = MDBoxLayout(orientation="vertical", spacing=dp(6), adaptive_height=True)

    header = MDLabel(text=f"{game_name}  [{'/'.join(spec.game_ids)}]", bold=True, size_hint_y=None, height=dp(24))
    group.add_widget(header)
    group.add_widget(_build_iso_row(game_name, spec))

    instance_field = MDTextField(
        MDTextFieldHintText(text="Instance (slot name you'll connect with)"),
        text="default", size_hint_x=0.5)
    instances_label, refresh_instances = _build_instances_label(spec)

    group.add_widget(_build_launch_controls(game_name, spec, instance_field, refresh_instances))
    group.add_widget(instances_label)
    return group


def build_bios_row() -> MDBoxLayout:
    """Shared across every game/instance Dynamic Pine launches, so one control
    here rather than duplicating it per game group. Always shows a
    "Change..." button (not just while unset, unlike the per-game ISO row)
    since re-pointing it is a reasonable thing to want to do later, not just a
    one-time setup step."""
    row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
    bios = get_bios_path()
    label = MDLabel(
        text=f"BIOS folder: {bios}" if bios is not None and bios.exists() else
             (f"BIOS folder: configured but not found at {bios}" if bios is not None
              else "BIOS folder: not set (each new instance will prompt for its own)"),
        shorten=True, shorten_from="left")
    row.add_widget(label)

    button = MDButton(MDButtonText(text="Change..."))

    def on_locate(_btn):
        chosen = prompt_for_bios()
        if chosen is not None:
            label.text = f"BIOS folder: {chosen}"

    button.bind(on_release=on_locate)
    row.add_widget(button)
    return row
