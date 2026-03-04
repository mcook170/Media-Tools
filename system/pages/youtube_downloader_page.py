# pages/youtube_downloader_page.py
import tkinter as tk
from tkinter import filedialog, messagebox
from numpy import double
from yt_dlp import YoutubeDL
import os, time, queue, threading, shutil
from ffmpeg_utils import get_ffmpeg_location

# debug: print when this module is imported so we know which file is executing
print(f"[DEBUG] loading youtube_downloader_page from {__file__}")

class YoutubeDownloaderPage(tk.Frame):
    def __init__(self, parent, download_queue: queue.Queue):
        super().__init__(parent, bg="#1e1e1e")
        self.download_queue = download_queue
        self.current_video_index = 0
        self.current_playlist_total = 0

        # Queue/task tracking
        # Number of tasks that have finished
        self.tasks_completed = 0
        # True while a task is actively being processed
        self.currently_processing_task = False
        # Number of individual videos/items that have finished downloading
        self.items_completed = 0
        
        # Download control flags
        self.stop_download = False
        self.pause_download = False
        self.skip_current_video = False
        self.current_task = None  # Store current task for reload functionality
        self.is_current_task_playlist = False  # Track if current task is a playlist

        # URL input
        tk.Label(self, text="YouTube URL:", bg="#1e1e1e", fg="white").pack(anchor="w", padx=10, pady=(10,0))
        self.url_entry = tk.Entry(self, width=60, bg="#2e2e2e", fg="white", insertbackground="white")
        self.url_entry.pack(padx=10, pady=5)

        # Output folder
        tk.Button(self, text="Select Output Folder", command=self.select_folder, bg="#2e2e2e", fg="white").pack(padx=10, pady=5)
        self.output_folder_label = tk.Label(self, text="No folder selected", bg="#1e1e1e", fg="white")
        self.output_folder_label.pack(anchor="w", padx=10)

        # Playlist toggle (allow manual override)
        self.playlist_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self, text="Download entire playlist if link is playlist", variable=self.playlist_var,
            bg="#1e1e1e", fg="white", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="white"
        ).pack(anchor="w", padx=10, pady=5)

        # Radio mode toggle
        self.radio_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self, text="Radio Mode (download only 1 song from playlist)", variable=self.radio_mode_var,
            bg="#1e1e1e", fg="white", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="white"
        ).pack(anchor="w", padx=10, pady=5)
        
        # Buttons for MP4 / MP3
        tk.Button(self, text="Download as MP4 (video file)", command=lambda: self.add_to_queue("mp4"), bg="#007acc", fg="white").pack(padx=10, pady=5)
        tk.Button(self, text="Download as MP3 (audio file)", command=lambda: self.add_to_queue("mp3"), bg="#007acc", fg="white").pack(padx=10, pady=5)

        # Control buttons frame (centered)
        control_frame = tk.Frame(self, bg="#1e1e1e")
        control_frame.pack(padx=10, pady=10, fill="x")

        # inner frame used to center the buttons horizontally
        inner_ctrl = tk.Frame(control_frame, bg="#1e1e1e")
        inner_ctrl.pack(anchor="center")

        # Use a consistent emoji-capable font and fixed width so icons render evenly
        tk.Button(inner_ctrl, text="◼", command=self.stop_current_download, bg="#1e1e1e", fg="white", width=3).pack(side="left")
        tk.Button(inner_ctrl, text="၊၊", command=self.pause_current_download, bg="#1e1e1e", fg="white", width=3).pack(side="left")
        tk.Button(inner_ctrl, text="▶", command=self.resume_download, bg="#1e1e1e", fg="white", width=3).pack(side="left")
        tk.Button(inner_ctrl, text="▶▶", command=self.skip_current_video_func, bg="#1e1e1e", fg="white", width=3).pack(side="left")
        tk.Button(inner_ctrl, text="🗘", command=self.reload_current_task, bg="#1e1e1e", fg="white", width=3).pack(side="left")

        # Label for In-Window Status Label
        self.status_label = tk.Label(self, text="", bg="#1e1e1e", fg="white")
        self.status_label.pack(anchor="w", padx=10, pady=(2,6))
        
        # Progress display
        self.progress_label = tk.Label(self, text="Current task: 0 of 0", bg="#1e1e1e", fg="white")
        self.progress_label.pack(anchor="w", padx=10, pady=(5,0))

        # Queue information panel (re-added)
        queue_info_frame = tk.LabelFrame(self, text="Queue Information", bg="#1e1e1e", fg="white", font=("Arial", 10, "bold"))
        queue_info_frame.pack(padx=5, pady=5, fill="both", expand=True)

        self.current_task_info = tk.Label(queue_info_frame, text="No active task", bg="#1e1e1e", fg="#88ccff", wraplength=500, justify="left")
        self.current_task_info.pack(anchor="w", padx=10, pady=5)

        listbox_label = tk.Label(queue_info_frame, text="Queued tasks:", bg="#1e1e1e", fg="white")
        listbox_label.pack(anchor="w", padx=10, pady=(5, 2))

        scrollbar = tk.Scrollbar(queue_info_frame)
        scrollbar.pack(side="right", fill="y")

        self.queue_listbox = tk.Listbox(queue_info_frame, bg="#2e2e2e", fg="white", height=6, yscrollcommand=scrollbar.set)
        self.queue_listbox.pack(padx=10, pady=5, fill="both", expand=True)
        scrollbar.config(command=self.queue_listbox.yview)

        # Start download thread
        self.downloader_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.downloader_thread.start()

    def set_status(self, text, fg="white"):
        self.after(0, lambda:
                   self.status_label.config(text=text, fg=fg))
        
    def clear_status(self):
        self.after(0, lambda: 
                   self.status_label.config(text=""))
        
    def stop_current_download(self):
        """Stop the current download immediately and clear the queue"""
        self.stop_download = True
        self.pause_download = False
        # Clear the download queue
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except queue.Empty:
                break
        self.set_status("Download stopped, and queue cleared.", fg="white")
        self.update_progress_label()
        self.update_queue_display()

    def pause_current_download(self):
        """Pause the current download"""
        self.pause_download = True
        self.set_status("Download Paused", fg="white")

    def resume_download(self):
        """Resume a paused download"""
        if self.pause_download:
            self.pause_download = False
            self.set_status("Download Resumed", fg="white")
        else:
            self.set_status("No Paused Download", fg="white")

    def reload_current_task(self):
        """Reload the current task back to the queue"""
        if self.current_task:
            self.download_queue.put(self.current_task)
            self.set_status("Task Reloaded", fg="white")
            self.update_progress_label()
            self.update_queue_display()
        else:
            self.set_status("No Active Task", fg="white")

    def skip_current_video_func(self):
        """Skip the current video and move to the next one"""
        if self.currently_processing_task and self.current_playlist_total > 1:
            self.skip_current_video = True
            self.set_status("Video Skipped", fg="white")
        elif self.currently_processing_task:
            self.set_status("Cannot Skip", fg="white")
        else:
            self.set_status("No Active Task", fg="white")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_label.config(text=folder)

    def add_to_queue(self, filetype):
        # debug: indicate this method is called and show current implementation
        print("[DEBUG] add_to_queue called")
        url = self.url_entry.get().strip()
        folder = self.output_folder_label.cget("text")
        if not url:
            self.set_status("Missing URL: Please enter a YouTube URL", fg="red")
            return
        if folder == "No folder selected":
            self.set_status("Missing Output Folder: Please select an output folder", fg="red")
            return

        task = {
            "url": url,
            "output": folder,
            "playlist": self.playlist_var.get(),
            "type": filetype,
            "radio_mode": self.radio_mode_var.get(),
            # default to a single item; we may overwrite below if a playlist is
            # detected and the user asked for it
            "num_items": 1
        }

        # if the user requested a playlist but supplied a watch URL that simply
        # contains ``?list=`` we convert it to the canonical playlist form
        # so yt-dlp will treat it correctly.  this avoids the annoying case
        # where the extractor returns a single video and num_items stays 1.
        if task["playlist"]:
            # look for a list=<id> parameter in the query string
            import urllib.parse
            parsed = urllib.parse.urlparse(task["url"])
            qs = urllib.parse.parse_qs(parsed.query)
            if "list" in qs and "playlist" not in parsed.path:
                # rebuild as the playlist URL
                listid = qs["list"][0]
                task["url"] = f"https://www.youtube.com/playlist?list={listid}"
                print(f"[DEBUG] normalized url to playlist form: {task['url']}")

        # only attempt to count entries if the playlist checkbox is checked
        if task["playlist"] and not task["radio_mode"]:
            try:
                with YoutubeDL({"quiet": True, "extract_flat": True, "ignoreerrors": True}) as ydl:
                    info = ydl.extract_info(task["url"], download=False)
                    if info and "entries" in info:
                        entries = [e for e in info["entries"] if e]
                        if entries:
                            task["num_items"] = len(entries)
                            print(f"[DEBUG] detected playlist length {task['num_items']}")
                        else:
                            print("[DEBUG] playlist info had zero entries")
                    else:
                        print("[DEBUG] info result has no entries key")
            except Exception as e:
                # detection failed; mark length unknown so the UI can show "?"
                print(f"[DEBUG] playlist detection exception: {e}")
                task["num_items"] = None
        elif task["radio_mode"]:
            # radio mode always counts as exactly one
            task["num_items"] = 1

        self.download_queue.put(task)
        print(f"[DEBUG] queued task: {task}")
        self.url_entry.delete(0, tk.END)
        self.update_progress_label()
        self.update_queue_display()

    def update_progress_label(self, current_idx=None, total_videos=None, percent=None):
        """Refresh the status text showing how many videos have been downloaded.

        The original implementation mixed "tasks" (user-submitted jobs) with
        individual video items, which led to confusing output whenever a
        playlist was treated as a single task.  We now normalise everything to
        item counts: the label always shows "Downloading item X of Y" when a
        download is active, and otherwise shows how many items remain queued.
        """

        # count every pending video across all queued tasks
        queued_items_count = 0
        if hasattr(self.download_queue, "queue"):
            for t in list(self.download_queue.queue):
                n = t.get("num_items")
                queued_items_count += n if isinstance(n, int) and n > 0 else 1

        # include the items belonging to the currently-processing task
        current_task_items = getattr(self, "current_task_total_items", 0) if self.currently_processing_task else 0

        total_items_pending = queued_items_count + (current_task_items if self.currently_processing_task else 0)
        overall_total_items = self.items_completed + total_items_pending

        print(f"[DEBUG] update_progress_label: items_completed={self.items_completed}, queued_items={queued_items_count}, current_task_items={current_task_items}, overall_total={overall_total_items}, current_idx={current_idx}, total_videos={total_videos}")

        # determine where we are within the overall sequence of items
        if self.currently_processing_task and current_idx is not None:
            # clamp current index against the reported total for this task
            bounded_current = current_idx
            if total_videos is not None and total_videos > 0:
                bounded_current = max(1, min(current_idx, total_videos))
            global_idx = self.items_completed + bounded_current
            overall_total_items = max(1, overall_total_items)  # avoid zero
            global_idx = max(1, min(global_idx, overall_total_items))

            percent = ((double (global_idx))/(double (overall_total_items)))*100
            if percent is not None:
                text = f"Downloading item {global_idx} of {overall_total_items} | {percent}%"
            else:
                text = f"Downloading item {global_idx} of {overall_total_items}"
        else:
            # no active download; show queue length or clear
            if queued_items_count:
                text = f"Queued items: {queued_items_count}"
            else:
                text = ""

        self.progress_label.config(text=text)

    def update_queue_display(self):
        """Refresh the queue panel with current and pending tasks."""
        # clear listbox first
        try:
            self.queue_listbox.delete(0, tk.END)
        except AttributeError:
            return  # UI not created yet

        # current task info
        if self.currently_processing_task and self.current_task:
            task_type = "Playlist" if self.is_current_task_playlist else "Single Video"
            radio_status = " [RADIO MODE]" if self.current_task.get("radio_mode", False) else ""
            current_info = f"Current: {task_type}{radio_status} | {self.current_playlist_total} video(s) | Type: {self.current_task['type'].upper()}"
            self.current_task_info.config(text=current_info)
        else:
            self.current_task_info.config(text="No active task")

        # queued tasks
        queued_tasks = list(self.download_queue.queue) if hasattr(self.download_queue, 'queue') else []
        if not queued_tasks:
            self.queue_listbox.insert(tk.END, "(No tasks queued)")
        else:
            for idx, task in enumerate(queued_tasks, 1):
                task_type = "Playlist" if task.get("playlist", False) else "Single"
                radio_mode = task.get("radio_mode", False)
                num_items = task.get("num_items", 1)
                # if for some reason we couldn't detect a length, show "?" so
                # the user knows it's unknown rather than silently 1
                if num_items is None or num_items < 1:
                    items_text = "? videos"
                elif num_items > 1:
                    items_text = f"{num_items} videos"
                else:
                    items_text = "1 video"
                radio_str = " [RADIO]" if radio_mode else ""
                task_str = f"{idx}. [{task_type}]{radio_str} {items_text} - {task['type'].upper()}"
                self.queue_listbox.insert(tk.END, task_str)

    def progress_hook(self, d):
        """yt-dlp progress hook for live updates in GUI"""
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            percent = int(downloaded_bytes / total_bytes * 100) if total_bytes else 0
            # Clamp current index to valid range before displaying
            total = max(1, self.current_playlist_total)
            idx = max(1, min(self.current_video_index or 1, total))
            self.update_progress_label(idx, self.current_playlist_total, percent)
        elif d['status'] == 'finished':
            # Move to next video index but don't exceed playlist total
            if self.current_video_index < self.current_playlist_total:
                self.current_video_index += 1
            else:
                # If already at or past total, keep it at total
                self.current_video_index = max(1, self.current_playlist_total)
            self.update_progress_label(self.current_video_index, self.current_playlist_total, 0)
            self.update_queue_display()

    def process_queue(self):
        while True:
            task = self.download_queue.get()
            if task is None or self.stop_download:
                if self.stop_download:
                    self.stop_download = False
                break
            
            # Store current task for reload functionality
            self.current_task = task
            # Mark that a task is starting
            self.currently_processing_task = True
            # Update UI to reflect task start (task number will be tasks_completed + 1)
            self.update_progress_label()
            self.update_queue_display()
            try:
                self.download_task(task)
            finally:
                # Task finished; item counts were already advanced inside download_task
                self.current_task_total_items = 0
                # Mark task-level bookkeeping
                self.tasks_completed += 1
                self.currently_processing_task = False
                self.download_queue.task_done()
                # Refresh UI to show updated queued/idle state
                self.update_progress_label()
                self.update_queue_display()

    def download_task(self, task):
        # Determine list of URLs
        urls_to_download = [task["url"]]
        
        # Check if radio mode is enabled
        if task.get("radio_mode", False):
            # In radio mode, try to extract playlist but only download first song
            try:
                with YoutubeDL({
                    "quiet": True,
                    "extract_flat": True,
                    "ignoreerrors": True,
                    "extractor_args": {"youtube": {"player_client": "default"}}
                }) as ydl:
                    info = ydl.extract_info(task["url"], download=False)
                    if "entries" in info:
                        # Get only the first entry
                        entries = [entry["url"] for entry in info["entries"] if entry]
                        if entries:
                            urls_to_download = [entries[0]]
            except Exception as e:
                print(f"Error extracting playlist: {e}")
        elif task["playlist"]:
            # Normal playlist mode - download all
            try:
                with YoutubeDL({
                    "quiet": True,
                    "extract_flat": True,
                    "ignoreerrors": True,
                    "extractor_args": {"youtube": {"player_client": "default"}}
                }) as ydl:
                    info = ydl.extract_info(task["url"], download=False)
                    if "entries" in info:
                        urls_to_download = [entry["url"] for entry in info["entries"] if entry]
            except Exception as e:
                print(f"Error extracting playlist: {e}")

        self.current_playlist_total = len(urls_to_download)
        self.is_current_task_playlist = task.get("radio_mode", False) or task["playlist"]
        self.current_video_index = 1  # first video
        # Track total items for this task so global counts can include it
        self.current_task_total_items = self.current_playlist_total
        # Display initial progress for this task (0% at start)
        self.update_progress_label(self.current_video_index, 
                                   self.current_playlist_total, 0)
        self.update_queue_display()

        # obtain ffmpeg path once before iterating; failure stops the whole task
        try:
            ffmpeg_loc = get_ffmpeg_location()
        except FileNotFoundError as e:
            messagebox.showerror(
                "FFmpeg not found",
                str(e)
                + "\n\nPut ffmpeg.exe and ffprobe.exe in the project's 'system' folder or install FFmpeg and add it to PATH.",
            )
            return

        for url in urls_to_download:
            # stop request takes priority
            if self.stop_download:
                print("Download stopped by user")
                return

            # skip request: count the skipped video as completed and adjust
            # our totals so that the global counters remain accurate
            if self.skip_current_video:
                self.skip_current_video = False
                print("Skipping current video")
                self.items_completed += 1
                self.current_task_total_items = max(0, self.current_task_total_items - 1)
                self.current_playlist_total = max(0, self.current_playlist_total - 1)
                # advance the per-task index (it will be clamped later)
                self.current_video_index += 1
                self.update_progress_label(self.current_video_index, self.current_playlist_total, 0)
                self.update_queue_display()
                continue

            # pause handling
            while self.pause_download:
                import time
                time.sleep(0.5)  # Sleep briefly and check again

            ydl_opts = {
                "format": "bestaudio/best" if task["type"] == "mp3" else "mp4/bestvideo+bestaudio/best",
                "outtmpl": os.path.join(task["output"], "%(title)s.%(ext)s"),
                "ignoreerrors": True,
                "quiet": True,
                "no_warnings": True,
                "ffmpeg_location": ffmpeg_loc,
                "extractor_args": {"youtube": {"player_client": "default"}},
                "progress_hooks": [self.progress_hook],
            }

            if task["type"] == "mp3":
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320"
                }]

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)

                # Cleanup non-MP3 sources
                if task["type"] == "mp3":
                    for f in os.listdir(task["output"]):
                        if f.startswith(ydl.prepare_filename({"title": f})) and not f.endswith(".mp3"):
                            os.remove(os.path.join(task["output"], f))

            except Exception as e:
                print(f"Error downloading {url}: {e}")
            finally:
                # one item has been handled (download or skip)
                self.items_completed += 1
                self.current_task_total_items = max(0, self.current_task_total_items - 1)
                self.current_video_index += 1
                self.update_progress_label(self.current_video_index, self.current_playlist_total, 0)
                self.update_queue_display()