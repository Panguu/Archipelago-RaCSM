from pathlib import Path
import threading

import kvui  # noqa: F401 (sets up Archipelago's Kivy config; must come before other Kivy imports)
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.utils import escape_markup
from Utils import local_path

from .container import SACPatch


class PatcherUI(App):
    """Patches on a background thread and shows how far along it is.

    Closes by itself when done. If patching fails, the error stays on screen
    until the window is closed, and `error` is set for the caller.
    """

    def __init__(self, patch: SACPatch, source: str, target: Path, branding: str):
        super().__init__()
        self.title = "Secret Agent Clank Patcher"
        self.icon = local_path("data", "icon.png")
        self.patch = patch
        self.source = source
        self.target = target
        self.branding = branding
        self.error: Exception | None = None
        self.done = False
        self.status = "Starting", 0.0  # set by the patching thread, shown by update()

    def build(self) -> BoxLayout:
        layout = BoxLayout(orientation="vertical", padding=24, spacing=12)
        layout.add_widget(Label(text="[b]Patching your Secret Agent Clank ISO[/b]\n"
                                     "This only happens once per patch build, and takes a few minutes.",
                                markup=True, halign="center"))
        self.message = Label(markup=True, halign="center", valign="middle")
        self.message.bind(size=lambda label, size: setattr(label, "text_size", size))
        layout.add_widget(self.message)
        self.bar = ProgressBar(max=1.0, size_hint_y=None, height=24)
        layout.add_widget(self.bar)
        self.percent = Label(size_hint_y=None, height=24)
        layout.add_widget(self.percent)
        Clock.schedule_interval(self.update, 1 / 30)
        return layout

    def on_start(self) -> None:
        threading.Thread(target=self.run_patch, daemon=True).start()

    def run_patch(self) -> None:
        try:
            self.patch.apply(self.source, self.target, self.branding, self.set_status)
        except Exception as error:
            self.error = error
        self.done = True

    def set_status(self, message: str, fraction: float) -> None:
        self.status = message, fraction

    def update(self, _dt: float):
        """Runs 30 times a second. Returning False stops it."""
        if self.done and self.error:
            self.message.text = (f"[color=#FF5555][size=20]Patching failed[/size]\n\n"
                                 f"{escape_markup(str(self.error))}[/color]\n\n"
                                 "[i]Close this window to carry on to the client.[/i]")
            return False
        if self.done:
            self.message.text = f"Done!\n\n{escape_markup(str(self.target))}"
            self.bar.value = 1.0
            self.percent.text = "100%"
            Clock.schedule_once(lambda _: self.stop(), 1.5)
            return False
        message, fraction = self.status
        self.message.text = f"{escape_markup(message)}..."
        self.bar.value = fraction
        self.percent.text = f"{fraction:.0%}"
