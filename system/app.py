# app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pages import youtube_downloader_page, metadata_editor_page
import queue
import threading
import sys
import os

# Add parent directory to path to import setup_binaries
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ffmpeg/ffprobe location is managed centrally in the
# ``ffmpeg_utils`` module.  The application itself doesn't reference it
# directly, so there's no need to compute this at import time.

# ``ydl_opts`` used to be constructed globally but was never consumed;
# the downloader page builds its own options dictionary per-task.
ydl_opts = {}

class App(tk.Tk):
    THEME = {
        "bg_dark": "#1e1e1e",
        "bg_menu": "#2e2e2e",
        "bg_button_active": "#555555",
        "bg_hover": "#007acc",
        "menu_font": ("Arial", 12),
    }
    def __init__(self):
        super().__init__()

        # Window and Title Settings
        self.title("Media Tools v2.1")
        self.geometry("800x500")
        self.configure(bg=self.THEME["bg_dark"])
        self.active_page = None

        # "Trigger" frame on the far left edge that will show the actual
        # sidebar when the mouse enters it.  We keep it narrow so it's mostly
        # invisible, but it's easier than trying to detect motion coordinates
        # on the root window.
        self.trigger_frame = tk.Frame(self, width=5, bg=self.THEME["bg_dark"])
        self.trigger_frame.pack(side="left", fill="y")
        self.trigger_frame.bind("<Enter>", lambda e: self.show_menu())

        # Left menu frame (hidden by default).  The show_menu()/hide_menu()
        # methods will pack/unpack it as the cursor moves in and out.
        self.menu_frame = tk.Frame(self, bg=self.THEME["bg_menu"], width=150)

        # Container for pages
        self.container = tk.Frame(self, bg=self.THEME["bg_dark"])
        self.container.pack(side="right", fill="both", expand=True)

        # Menu buttons dictionary
        self.menu_buttons = {}

        # track whether the sidebar is currently visible; we don't want to
        # repack it repeatedly
        self._menu_visible = False

        # Queue for downloads
        self.download_queue = queue.Queue()

        # Pages dictionary
        self.pages = {}
        self.register_pages()

        # Build menu (does not pack it yet)
        self.build_menu()

        # Initially the menu is hidden; the trigger frame takes its place.  The
        # menu will appear when the user hovers over the trigger or stays in the
        # menu area.
        #
        # We also bind a leave event so that moving the cursor out of the menu
        # hides it again.  A short delay prevents it from closing while the
        # pointer is transitioning back to the trigger frame.
        self.menu_frame.bind("<Leave>", lambda e: self.after(100, self._check_hide))

        # Show default page
        self.show_page("YouTube Downloader")

    # Pages on Sidebar Menu
    def register_pages(self):
        self.pages["YouTube Downloader"] = youtube_downloader_page.YoutubeDownloaderPage(
            self.container, self.download_queue
        )
        self.pages["Metadata Editor"] = metadata_editor_page.MetadataEditorPage(
            self.container
        )

    # Menu Buttons and Mouse Actions
    def build_menu(self):
        for page_name in self.pages:
            btn = tk.Label(
                self.menu_frame, text=page_name, bg=self.THEME["bg_menu"], fg="white",
                font=self.THEME["menu_font"], padx=10, pady=10, cursor="hand2"
            )
            btn.pack(fill="x", pady=2)
            btn.bind("<Button-1>", lambda e, name=page_name: self.show_page(name))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.THEME["bg_hover"]))
            btn.bind("<Leave>", lambda e, b=btn, name=page_name: b.config(
                bg=self.THEME["bg_button_active"] if self.active_page == name else self.THEME["bg_menu"]))
            self.menu_buttons[page_name] = btn

    # Sidebar visibility helpers
    def show_menu(self):
        if not self._menu_visible:
            self.menu_frame.pack(side="left", fill="y")
            self._menu_visible = True

    def hide_menu(self):
        if self._menu_visible:
            self.menu_frame.pack_forget()
            self._menu_visible = False

    def _check_hide(self):
        # only hide if the cursor is neither in the menu nor the trigger
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if widget not in (self.menu_frame, self.trigger_frame):
            self.hide_menu()

    # Show/Hide Page
    def show_page(self, page_name):
        # Hide current page and show new page
        if self.active_page:
            self.pages[self.active_page].pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)

        # Update Button Colors
        if self.active_page:
            self.menu_buttons[self.active_page].config(bg=self.THEME["bg_menu"])
        self.menu_buttons[page_name].config(bg=self.THEME["bg_button_active"])
        self.active_page = page_name


if __name__ == "__main__":
    app = App()
    app.mainloop()