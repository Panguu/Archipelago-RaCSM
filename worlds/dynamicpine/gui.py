from typing import Callable

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dropdownitem import MDDropDownItem, MDDropDownItemText
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kvui import MDLabel

from CommonClient import logger
from Utils import open_filename

from .api import (DynamicPineGame, get_bios_path, get_iso_options, get_selected_iso_name, remove_iso,
                  set_selected_iso)
from .context import _LAUNCH_ERRORS, launch_game_client, launch_simple
from .launcher import clear_unused_instances, launch_pcsx2, list_instances, prompt_for_bios, prompt_for_iso


def _build_iso_row(game_name: str, spec: DynamicPineGame) -> MDBoxLayout:
    row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))

    selected_text = MDDropDownItemText(text="")
    dropdown = MDDropDownItem(selected_text, size_hint_x=None, width=dp(160))
    path_label = MDLabel(text="", shorten=True, shorten_from="left")
    add_button = MDButton(MDButtonText(text="Add ISO..."))
    remove_button = MDButton(MDButtonText(text="Remove"))

    def refresh() -> None:
        options = get_iso_options(spec)
        selected = get_selected_iso_name(spec)
        selected_text.text = selected or "No ISO"
        remove_button.disabled = selected is None
        if selected is None:
            path_label.text = "ISO: not found - add one"
        elif options[selected].exists():
            path_label.text = str(options[selected])
        else:
            path_label.text = f"Not found at {options[selected]}"

    def on_open(_item) -> None:
        def on_select(name: str) -> None:
            menu.dismiss()
            set_selected_iso(spec, name)
            refresh()

        items = [{"text": name, "on_release": lambda n=name: on_select(n)} for name in get_iso_options(spec)]
        if items:
            menu = MDDropdownMenu(caller=dropdown, items=items)
            menu.open()

    def on_add(_btn) -> None:
        if prompt_for_iso(game_name, spec) is not None:
            refresh()

    def on_remove(_btn) -> None:
        selected = get_selected_iso_name(spec)
        if selected is not None:
            remove_iso(spec, selected)
            refresh()

    dropdown.bind(on_release=on_open)
    add_button.bind(on_release=on_add)
    remove_button.bind(on_release=on_remove)

    row.add_widget(dropdown)
    row.add_widget(path_label)
    row.add_widget(add_button)
    row.add_widget(remove_button)
    refresh()
    return row


def _build_instances_label(spec: DynamicPineGame) -> tuple[MDLabel, Callable[[], None]]:
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
        # One button that launches PCSX2 and the client together
        launch_button = MDButton(MDButtonText(text="Launch"))
        launch_button.bind(on_release=on_launch_simple)
        controls.add_widget(launch_button)
    elif spec.launcher_options == "patch" and spec.client_component:
        # Like "client", but prompts for the per-seed patch file and passes it to the client
        patch_button = MDButton(MDButtonText(text="Patch & Launch"))
        patch_button.bind(on_release=on_patch_and_launch)
        controls.add_widget(patch_button)
    elif spec.launcher_options == "client" and spec.client_component:
        # The client launches PCSX2 itself, so the hub only starts the client
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
