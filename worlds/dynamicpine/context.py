from typing import TYPE_CHECKING

from CommonClient import ClientCommandProcessor, CommonContext, logger
from worlds.LauncherComponents import components, launch

from .api import (
    DynamicPineGame,
    discover_games,
    get_bios_path,
    get_iso_path,
    mark_pcsx2_already_launched,
    mark_pending_auth,
)
from .launcher import (
    InstanceAlreadyRunningError,
    NoBiosConfigured,
    NoIsoConfigured,
    NoPCSX2Executable,
    clear_unused_instances,
    ensure_instance_config,
    launch_pcsx2,
    list_instances,
    prompt_for_bios,
)
from .world import DYNAMIC_PINE_VERSION

if TYPE_CHECKING:
    from kvui import GameManager

__all__ = ["DynamicPineCommandProcessor", "DynamicPineContext"]

_LAUNCH_ERRORS = (InstanceAlreadyRunningError, NoPCSX2Executable, NoIsoConfigured, NoBiosConfigured)


def _match_game(query: str) -> tuple[str, DynamicPineGame] | None:
    games = discover_games()
    if query in games:
        return query, games[query][1]
    lowered = query.lower()
    if not lowered:
        return None
    matches = [(name, spec) for name, (_, spec) in games.items()
               if lowered in name.lower() or lowered in (gid.lower() for gid in spec.game_ids)]
    return matches[0] if len(matches) == 1 else None


def launch_game_client(spec: DynamicPineGame, game_name: str, instance: str | None = None,
                       patch_file: str | None = None) -> bool:
    if not spec.client_component:
        logger.warning(f"[DynamicPine] {game_name} does not declare a client_component to launch.")
        return False

    if instance:
        mark_pending_auth(instance)

    try:
        ensure_instance_config(spec, instance)
    except Exception as exc:
        logger.warning(f"[DynamicPine] Could not prepare instance config for {game_name}: {exc}")

    for component in components:
        if component.display_name == spec.client_component and component.func is not None:
            launch(component.func, name=component.display_name,
                   args=(patch_file,) if patch_file else ())
            return True
    logger.warning(f"[DynamicPine] No launchable component named {spec.client_component!r} found.")
    return False


def launch_simple(spec: DynamicPineGame, game_name: str, instance: str | None = None) -> bool:
    try:
        launch_pcsx2(game_name, instance)
    except InstanceAlreadyRunningError:
        pass  # already running is fine, the client just connects to it
    except Exception as exc:
        logger.warning(f"[DynamicPine] Could not launch PCSX2 for {game_name}: {exc}")
        return False
    mark_pcsx2_already_launched()
    return launch_game_client(spec, game_name, instance)


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
            self.output(f"{game_name} [{'/'.join(spec.game_ids)}] - "
                        f"{iso if iso else 'no ISO configured in host.yaml'}")
            for inst in list_instances(spec):
                status = f"running (pid {inst.pid})" if inst.running else "stopped"
                self.output(f"    {inst.instance_id} (PINE port {inst.port}) - {status}")
        return True

    def _cmd_launch(self, game_name: str = "", instance: str = "", patch_file: str = "") -> bool:
        """Launch a Dynamic Pine game's own client.
        patch_file is only needed for launcher_options="patch" games."""
        match = _match_game(game_name)
        if match is None:
            self.output(f"Unknown or ambiguous game {game_name!r} - see /games for the list.")
            return False
        return launch_game_client(match[1], match[0], instance or None, patch_file or None)

    def _cmd_launch_pcsx2(self, game_name: str = "", instance: str = "") -> bool:
        """Launch a PCSX2 instance for a Dynamic Pine game without its client.
        Instance should match the slot name you'll connect with (default: "default")."""
        match = _match_game(game_name)
        if match is None:
            self.output(f"Unknown or ambiguous game {game_name!r} - see /games for the list.")
            return False
        try:
            return launch_pcsx2(match[0], instance or None) is not None
        except _LAUNCH_ERRORS as exc:
            self.output(f"[DynamicPine] {exc}")
            return False

    def _cmd_clear(self, game_name: str = "") -> bool:
        """Remove every stopped Dynamic Pine instance for a game. Running instances are left alone."""
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
    # Never connects to a server - only a CommonContext so kvui's GameManager works
    command_processor = DynamicPineCommandProcessor
    game = ""

    def make_gui(self) -> "type[GameManager]":
        ui = super().make_gui()  # before the kivy imports so kvui gets loaded first

        class DynamicPineManager(ui):
            base_title = f"Dynamic Pine {DYNAMIC_PINE_VERSION} hub for AP version"

            def build(self):
                container = super().build()
                # Drop the server bar and Hints tab; ignore failures if kvui's layout changes
                try:
                    self.grid.remove_widget(self.connect_layout)
                    self.grid.remove_widget(self.progressbar)
                    self.grid.remove_widget(self.textinput)
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
        # kivy must only be imported after make_gui has loaded kvui
        from kivy.metrics import dp
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.scrollview import MDScrollView

        from kvui import MDDivider, MDLabel

        from .gui import build_bios_row, build_game_group

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
