"""Dynamic Pine hub client: one tab per installed Dynamic Pine game, with
controls to launch PCSX2 instances and each game's own client. The games'
clients are untouched - the hub only starts them (as subprocesses when the GUI
is running), and everything from there onwards is their existing logic.

Structure modeled on Universal Tracker's client (context subclass wrapping
super().make_gui(), tabs added via kvui's GameManager.add_client_tab) with
CommonClient handling everything underneath."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, logger

from . import DYNAMIC_PINE_VERSION
from .api import DynamicPineGame, discover_games, get_bios_path, get_iso_path
from .launcher import (InstanceAlreadyRunningError, clear_unused_instances, ensure_instance_config,
                       launch_pcsx2, list_instances, prompt_for_bios, prompt_for_iso)

if TYPE_CHECKING:
    from kvui import GameManager

__all__ = ["DynamicPineContext", "DynamicPineCommandProcessor", "run_client"]


def _match_game(query: str) -> tuple[str, DynamicPineGame] | None:
    """Finds a single installed Dynamic Pine game by exact name, serial, or
    unambiguous case-insensitive substring - None if nothing (or more than one
    thing) matches."""
    games = discover_games()
    if query in games:
        return query, games[query][1]
    lowered = query.lower()
    if not lowered:
        return None
    matches = [(name, spec) for name, (_, spec) in games.items()
               if lowered in name.lower() or lowered == spec.game_id.lower()]
    return matches[0] if len(matches) == 1 else None


def launch_game_client(spec: DynamicPineGame, game_name: str, instance: str | None = None) -> bool:
    """Starts the game's own registered client component. Nothing about that
    client changes from here onwards - it connects, resolves its slot name, and
    calls back into Dynamic Pine itself for its PCSX2/PINE port.

    Prepares this instance's PCSX2 config (ensure_instance_config) before
    starting the client, even though the client isn't launched here -
    previously that only happened as a side effect of the "Launch PCSX2"
    button, so a client started on its own had no instance settings to pick up
    until it made its own launch_pcsx2 call later."""
    if not spec.client_component:
        logger.warning(f"[DynamicPine] {game_name} does not declare a client_component to launch.")
        return False

    try:
        ensure_instance_config(spec, instance)
    except Exception as exc:
        logger.warning(f"[DynamicPine] Could not prepare instance config for {game_name}: {exc}")

    from worlds.LauncherComponents import components, launch
    for component in components:
        if component.display_name == spec.client_component and component.func is not None:
            launch(component.func, name=component.display_name)
            return True
    logger.warning(f"[DynamicPine] No launchable component named {spec.client_component!r} found.")
    return False


class DynamicPineCommandProcessor(ClientCommandProcessor):
    ctx: "DynamicPineContext"

    def _cmd_games(self) -> bool:
        """List installed Dynamic Pine games, their configured ISOs, and running PCSX2 instances."""
        games = discover_games()
        if not games:
            self.output("No installed worlds declare Dynamic Pine support.")
            return True
        for game_name, (_, spec) in sorted(games.items()):
            iso = get_iso_path(spec)
            self.output(f"{game_name} [{spec.game_id}] - "
                        f"{iso if iso else 'no ISO configured in host.yaml'}")
            for inst in list_instances(spec):
                status = f"running (pid {inst.pid})" if inst.running else "stopped"
                self.output(f"    {inst.instance_id} (PINE port {inst.port}) - {status}")
        return True

    def _cmd_launch(self, game_name: str = "", instance: str = "") -> bool:
        """Launch a Dynamic Pine game's own client (which handles PCSX2 itself once connected)."""
        match = _match_game(game_name)
        if match is None:
            self.output(f"Unknown or ambiguous game {game_name!r} - see /games for the list.")
            return False
        return launch_game_client(match[1], match[0], instance or None)

    def _cmd_launch_pcsx2(self, game_name: str = "", instance: str = "") -> bool:
        """Launch a PCSX2 instance for a Dynamic Pine game without its client.
        Instance should match the slot name you'll connect with (default: "default")."""
        match = _match_game(game_name)
        if match is None:
            self.output(f"Unknown or ambiguous game {game_name!r} - see /games for the list.")
            return False
        try:
            return launch_pcsx2(match[0], instance or None) is not None
        except InstanceAlreadyRunningError as exc:
            self.output(f"[DynamicPine] {exc}")
            return False

    def _cmd_clear(self, game_name: str = "") -> bool:
        """Remove every stopped (not currently running) Dynamic Pine instance
        for a game, freeing up their disk space/ports. Running instances are
        left untouched."""
        match = _match_game(game_name)
        if match is None:
            self.output(f"Unknown or ambiguous game {game_name!r} - see /games for the list.")
            return False
        removed = clear_unused_instances(match[1])
        self.output(f"Removed {len(removed)} unused instance(s) for {match[0]}: "
                    f"{', '.join(removed) if removed else '(none)'}")
        return True

    def _cmd_bios(self) -> bool:
        """Show or set the shared PCSX2 BIOS folder used by every Dynamic Pine game/instance."""
        bios = get_bios_path()
        if bios is not None:
            self.output(f"BIOS folder: {bios}" + ("" if bios.exists() else " (not found)"))
        else:
            self.output("BIOS folder: not set - each new instance will prompt for its own.")
        chosen = prompt_for_bios()
        if chosen is not None:
            self.output(f"BIOS folder set to: {chosen}")
        return True


class DynamicPineContext(CommonContext):
    """The hub never connects to an AP server itself - it only launches PCSX2
    instances and other games' clients (which do their own connecting). It's
    still a CommonContext so kvui's GameManager machinery (tabs, log pane,
    /command input) works unchanged underneath; the server/hints parts of that
    GUI are stripped in make_gui and no server loop is ever started."""
    command_processor = DynamicPineCommandProcessor
    game = ""  # the hub is not tied to any one game

    def make_gui(self) -> "type[GameManager]":
        ui = super().make_gui()  # before the kivy imports so kvui gets loaded first

        class DynamicPineManager(ui):
            base_title = f"Dynamic Pine {DYNAMIC_PINE_VERSION} hub for AP version"

            def build(self):
                container = super().build()
                # No server connection or hints here - drop the connect bar, its
                # progress indicator, and the Hints tab that GameManager builds
                # for regular clients. Defensive try/excepts so a kvui layout
                # change degrades to showing the stock widgets rather than
                # killing the hub.
                try:
                    self.grid.remove_widget(self.connect_layout)
                    self.grid.remove_widget(self.progressbar)
                except Exception:
                    pass
                try:
                    hints_tab = next(tab for tab in self.tabs.children
                                     if getattr(tab, "text", None) == "Hints")
                    self.remove_client_tab(hints_tab)
                except Exception:
                    pass
                self.ctx.build_gui(self)
                return container

        return DynamicPineManager

    def build_gui(self, manager: "GameManager") -> None:
        """Adds one "Dynamic Pine" tab (same add_client_tab mechanism Universal
        Tracker uses for its Tracker/Map pages) containing a scrollable column
        with a group of controls for each installed Dynamic Pine game."""
        from kivy.clock import Clock
        from kivy.metrics import dp
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDButton, MDButtonText
        from kivymd.uix.scrollview import MDScrollView
        from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
        from kvui import MDDivider, MDLabel

        def build_game_group(game_name: str, spec: DynamicPineGame):
            group = MDBoxLayout(orientation="vertical", spacing=dp(6),
                                adaptive_height=True)

            header = MDLabel(text=f"{game_name}  [{spec.game_id}]", bold=True,
                             size_hint_y=None, height=dp(24))
            group.add_widget(header)

            # ISO row: status label, plus a locate button while the game file
            # isn't detected - choosing one persists to host.yaml and the
            # button disappears.
            iso_row = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                                  size_hint_y=None, height=dp(40))
            iso = get_iso_path(spec)
            iso_detected = iso is not None and iso.exists()
            iso_label = MDLabel(
                text=f"ISO: {iso}" if iso_detected else
                     (f"ISO: configured but not found at {iso}" if iso else "ISO: not found"),
                shorten=True, shorten_from="left")
            iso_row.add_widget(iso_label)

            if not iso_detected:
                locate_button = MDButton(MDButtonText(text="Locate ISO..."))

                def on_locate(_btn, s=spec, g=game_name, label=iso_label, row=iso_row,
                              btn=locate_button):
                    chosen = prompt_for_iso(g, s)
                    if chosen is not None:
                        label.text = f"ISO: {chosen}"
                        row.remove_widget(btn)

                locate_button.bind(on_release=on_locate)
                iso_row.add_widget(locate_button)
            group.add_widget(iso_row)

            controls = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                                   size_hint_y=None, height=dp(56))
            instance_field = MDTextField(
                MDTextFieldHintText(text="Instance (slot name you'll connect with)"),
                text="default", size_hint_x=0.5)
            controls.add_widget(instance_field)

            instances_label = MDLabel(text="Instances: checking...",
                                      size_hint_y=None, height=dp(24))

            def refresh(_dt=None, s=spec, label=instances_label):
                try:
                    instances = list_instances(s)
                except Exception as exc:
                    label.text = f"Instances: unavailable ({exc})"
                    return
                label.text = ("Instances: " + ", ".join(
                    f"{i.instance_id} (port {i.port}, {'running' if i.running else 'stopped'})"
                    for i in instances)) if instances else "Instances: none created yet"

            def on_launch_pcsx2(_btn, g=game_name, field=instance_field):
                try:
                    launch_pcsx2(g, field.text or None)
                except InstanceAlreadyRunningError as exc:
                    logger.warning(f"[DynamicPine] {exc}")
                refresh()

            def on_clear_unused(_btn, s=spec, g=game_name):
                removed = clear_unused_instances(s)
                logger.info(f"[DynamicPine] Removed {len(removed)} unused instance(s) for {g}: "
                           f"{', '.join(removed) if removed else '(none)'}")
                refresh()

            pcsx2_button = MDButton(MDButtonText(text="Launch PCSX2"))
            pcsx2_button.bind(on_release=on_launch_pcsx2)
            controls.add_widget(pcsx2_button)

            if spec.client_component:
                client_button = MDButton(MDButtonText(text="Launch Client"))
                client_button.bind(on_release=lambda _btn, s=spec, g=game_name, field=instance_field:
                                   launch_game_client(s, g, field.text or None))
                controls.add_widget(client_button)

            clear_button = MDButton(MDButtonText(text="Clear Unused"))
            clear_button.bind(on_release=on_clear_unused)
            controls.add_widget(clear_button)
            group.add_widget(controls)

            Clock.schedule_interval(refresh, 3)
            refresh()
            group.add_widget(instances_label)
            return group

        def build_bios_row():
            # Shared across every game/instance Dynamic Pine launches - one
            # control here rather than duplicating it per game group. Always
            # shows a "Change..." button (not just while unset, unlike the
            # per-game ISO row) since re-pointing it is a reasonable thing to
            # want to do later, not just a one-time setup step.
            row = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                              size_hint_y=None, height=dp(40))
            bios = get_bios_path()
            bios_label = MDLabel(
                text=f"BIOS folder: {bios}" if bios is not None and bios.exists() else
                     (f"BIOS folder: configured but not found at {bios}" if bios is not None
                      else "BIOS folder: not set (each new instance will prompt for its own)"),
                shorten=True, shorten_from="left")
            row.add_widget(bios_label)

            bios_button = MDButton(MDButtonText(text="Change..."))

            def on_locate(_btn, label=bios_label):
                chosen = prompt_for_bios()
                if chosen is not None:
                    label.text = f"BIOS folder: {chosen}"

            bios_button.bind(on_release=on_locate)
            row.add_widget(bios_button)
            return row

        column = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(16),
                             adaptive_height=True)
        column.add_widget(build_bios_row())
        column.add_widget(MDDivider(size_hint_y=None, height=dp(1)))
        games = discover_games()
        if not games:
            column.add_widget(MDLabel(
                text="No installed worlds declare Dynamic Pine support.\n"
                     "Install a Dynamic Pine enabled apworld and relaunch this client.",
                halign="center", size_hint_y=None, height=dp(64)))
        else:
            for index, (game_name, (_, spec)) in enumerate(sorted(games.items())):
                if index:
                    column.add_widget(MDDivider(size_hint_y=None, height=dp(1)))
                column.add_widget(build_game_group(game_name, spec))

        scroll = MDScrollView()
        scroll.add_widget(column)
        manager.add_client_tab("Dynamic Pine", scroll)


async def main() -> None:
    # No server_loop task on purpose - the hub has nothing to say to an AP
    # server. The games' own clients it launches handle their own connections.
    ctx = DynamicPineContext(None, None)

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()


def run_client(*args: str) -> None:
    from Utils import init_logging

    init_logging("DynamicPineClient")

    # Marks this process (and, since it's inherited, any game client this hub
    # later spawns via launch_game_client) as legitimately "Dynamic Pine" -
    # launch_pcsx2 refuses to do anything without it. Set as early as
    # possible so it's in place before anything below could spawn a child.
    from .api import mark_launched_via_hub
    mark_launched_via_hub()

    # Base parser kept so standard flags like --nogui work; any connection args
    # it accepts are simply ignored.
    parser = get_base_parser(description="Dynamic Pine hub client")
    parser.parse_args(args)

    import colorama

    colorama.just_fix_windows_console()
    asyncio.run(main())
    colorama.deinit()
