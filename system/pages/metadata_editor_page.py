# pages/metadata_editor_page.py
import tkinter as tk
import keyboard
from tkinter import filedialog, messagebox
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import os

class MetadataEditorPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e")
        
        self.current_file = None
        self.current_folder = None
        self.audio = None
        self.folder_files = []
        self.current_file_index = 0
        # track cover art selection and removal flag
        self.selected_cover_art = None
        self.remove_cover_art = False
        # remember whether we've already prompted for a folder.jpg on
        # the current folder.  ``apply_all_choice`` holds the user's
        # response (True/False) or None if we haven't asked yet.
        self.apply_all_choice = None
        
        # File/Folder selection frame
        file_frame = tk.Frame(self, bg="#1e1e1e")
        file_frame.pack(padx=10, pady=10, fill="x")
        
        tk.Button(file_frame, text="Select MP3 File", command=self.select_file,
                  bg="#007acc", fg="white", width=15).pack(side="left", padx=2)
        
        tk.Button(file_frame, text="Select Folder", command=self.select_folder,
                  bg="#0056b3", fg="white", width=15).pack(side="left", padx=2)
        
        self.file_label = tk.Label(file_frame, text="No file/folder selected", bg="#1e1e1e", fg="white")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        
        # Navigation frame (for folder mode)
        nav_frame = tk.Frame(self, bg="#1e1e1e")
        nav_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Button(nav_frame, text="< Previous", command=self.prev_file,
                  bg="#555555", fg="white", width=12).pack(side="left", padx=2)
        
        self.nav_label = tk.Label(nav_frame, text="", bg="#1e1e1e", fg="white")
        self.nav_label.pack(side="left", padx=10, fill="x", expand=True)
        
        tk.Button(nav_frame, text="Next >", command=self.next_file,
                  bg="#555555", fg="white", width=12).pack(side="left", padx=2)
        
        # delete current file button
        tk.Button(nav_frame, text="⦸", command=self.delete_current_file,
                  bg="#d9534f", fg="white", justify="center").pack(expand=True)
        
        # Metadata editing frame
        edit_frame = tk.LabelFrame(self, text="Edit Metadata", bg="#1e1e1e", fg="white", 
                                    font=("Arial", 10, "bold"))
        edit_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create editable fields (text only)
        self.fields = {}
        field_names = ["Artist", "Title", "Album", "Genre", "Date"]
        
        for field in field_names:
            tk.Label(edit_frame, text=f"{field}:", bg="#1e1e1e", fg="white").pack(anchor="w", padx=10, pady=(5, 0))
            entry = tk.Entry(edit_frame, width=50, bg="#2e2e2e", fg="white", insertbackground="white")
            entry.pack(padx=10, pady=3, fill="x")

            self.fields[field] = entry
        
        # cover art picker and track number on same line
        cover_frame = tk.Frame(edit_frame, bg="#1e1e1e")
        cover_frame.pack(anchor="w", padx=10, pady=(5,0), fill="x")
        tk.Label(cover_frame, text="Cover Art:", bg="#1e1e1e", fg="white").pack(side="left")
        tk.Button(cover_frame, text="Select Image...", command=self.select_cover_art,
                  bg="#007acc", fg="white").pack(side="left", padx=(5,2))
        tk.Button(cover_frame, text="Clear", command=self.clear_cover_art,
                  bg="#555555", fg="white").pack(side="left", padx=(2,5))
        self.cover_art_filename = tk.Label(cover_frame, text="None", bg="#1e1e1e", fg="white")
        self.cover_art_filename.pack(side="left", padx=5)

        # track number entry on same line
        tk.Label(cover_frame, text="Track #:", bg="#1e1e1e", fg="white").pack(side="left", padx=(20,2))
        self.track_entry = tk.Entry(cover_frame, width=5, bg="#2e2e2e", fg="white", insertbackground="white")
        self.track_entry.pack(side="left", padx=(0,5))
        
        # Status label
        self.status_label = tk.Label(self, text="", bg="#1e1e1e", fg="white")
        self.status_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Save buttons frame (always visible)
        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(padx=10, pady=10, fill="x")
        tk.Button(button_frame, text="Apply to All (Ctrl+A)", command=self.apply_all_files,
                  bg="#28a745", fg="white").pack(side="left", padx=5, expand=True, fill="x")
        tk.Button(button_frame, text="Apply to Current (Ctrl+O)", command=self.apply_current_file,
                  bg="#555555", fg="white").pack(side="left", padx=5, expand=True, fill="x")
        
        # arrow-key navigation for folder files
        self.bind_all("<Left>", lambda e: self.prev_file())
        self.bind_all("<Right>", lambda e: self.next_file())
        self.bind('Enter', self.next_file())
        keyboard.add_hotkey('ctrl+a', self.apply_all_files)
        keyboard.add_hotkey('ctrl+o', self.apply_current_file)
        self.bind('Delete', self.delete_current_file)
    
    def set_status(self, text, fg="white"):
        """Update status label"""
        self.status_label.config(text=text, fg=fg)

    def select_cover_art(self):
        """Prompt user to pick an image file for cover art"""
        path = filedialog.askopenfilename(
            title="Select cover art image",
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png")]
        )
        if not path:
            return
        self.selected_cover_art = path
        self.remove_cover_art = False
        self.cover_art_filename.config(text=os.path.basename(path))

    def clear_cover_art(self):
        """Clear any selected cover art (remove on save)"""
        self.selected_cover_art = None
        self.remove_cover_art = True
        self.cover_art_filename.config(text="None")
    
    def select_file(self):
        """Browse for single MP3 file"""
        file_path = filedialog.askopenfilename(
            title="Select MP3 file",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.current_file = file_path
        self.current_folder = None
        self.folder_files = []
        self.file_label.config(text=os.path.basename(file_path))
        self.nav_label.config(text="")
        self.load_metadata()

    
    def select_folder(self):
        """Browse for folder (album) with MP3 files"""
        folder_path = filedialog.askdirectory(title="Select folder with MP3 files")
        
        if not folder_path:
            return
        
        # Reset any previous prompt state when choosing a new folder
        if folder_path != self.current_folder:
            self.apply_all_choice = None

        # Find all MP3 files in folder
        mp3_files = [f for f in os.listdir(folder_path) if f.endswith(".mp3")]
        
        if not mp3_files:
            self.set_status("No MP3 files found in folder", fg="orange")
            return
        
        self.current_folder = folder_path
        self.current_file = None
        self.folder_files = sorted([os.path.join(folder_path, f) for f in mp3_files])
        self.current_file_index = 0
        
        self.file_label.config(text=os.path.basename(folder_path))
        self.load_metadata()
        self.update_nav_label()

        # Auto-detect folder.jpg as cover art
        folder_jpg = os.path.join(folder_path, "folder.jpg")
        if os.path.exists(folder_jpg):
            # if any file already contains artwork we skip the prompt entirely
            already_has_art = False
            for f in self.folder_files:
                try:
                    id3 = ID3(f)
                    if id3.getall("APIC"):
                        already_has_art = True
                        break
                except Exception:
                    pass

            # only ask once per folder and only if no file already has art
            if not already_has_art and self.apply_all_choice is None:
                self.selected_cover_art = folder_jpg
                self.remove_cover_art = False
                self.cover_art_filename.config(text="folder.jpg")
                try:
                    apply_now = messagebox.askyesno(
                        "Apply cover art",
                        "A 'folder.jpg' was found in this folder. Apply it to all songs now?"
                    )
                except Exception:
                    apply_now = False

                # remember the answer so we don't prompt again on re‑select
                self.apply_all_choice = apply_now

                if apply_now:
                    # only write cover art; don't touch any other tags
                    self._apply_cover_to_files(self.folder_files, folder_jpg)
    
    def update_nav_label(self):
        """Update navigation label for folder mode"""
        if self.folder_files:
            total = len(self.folder_files)
            current = self.current_file_index + 1
            filename = os.path.basename(self.folder_files[self.current_file_index])
            self.nav_label.config(text=f"File {current} of {total}: {filename}")
    
    def prev_file(self):
        """Go to previous file in folder"""
        if not self.folder_files or len(self.folder_files) <= 1:
            return
        
        self.current_file_index = (self.current_file_index - 1) % len(self.folder_files)
        self.load_metadata()
        self.update_nav_label()

    def delete_current_file(self):
        """Remove/delete the currently selected file"""
        # determine path
        if self.folder_files:
            path = self.folder_files[self.current_file_index]
        elif self.current_file:
            path = self.current_file
        else:
            return
        # confirm
        if not messagebox.askyesno("Delete file", f"Delete '{os.path.basename(path)}'?\nThis will remove it from the folder and delete from disk."):
            return
        try:
            os.remove(path)
        except Exception as e:
            self.set_status(f"Error deleting: {e}", fg="red")
            return
        # update lists
        if self.folder_files:
            del self.folder_files[self.current_file_index]
            if self.folder_files:
                self.current_file_index %= len(self.folder_files)
                self.load_metadata()
            else:
                self.current_file = None
                self.file_label.config(text="No file/folder selected")
        else:
            self.current_file = None
            self.file_label.config(text="No file/folder selected")
        self.update_nav_label()
    
    def next_file(self):
        """Go to next file in folder"""
        if not self.folder_files or len(self.folder_files) <= 1:
            return
        
        self.current_file_index = (self.current_file_index + 1) % len(self.folder_files)
        self.load_metadata()
        self.update_nav_label()
    
    def load_metadata(self):
        """Load metadata from MP3 file"""
        # Determine which file to load from
        if self.folder_files:
            file_path = self.folder_files[self.current_file_index]
        elif self.current_file:
            file_path = self.current_file
        else:
            return
        
        try:
            # Try to load with EasyID3 (user-friendly)
            audio = EasyID3(file_path)
            self.audio = audio
            
            # Clear all fields first
            for field in self.fields:
                self.fields[field].delete(0, tk.END)
            # clear track entry as well
            if hasattr(self, 'track_entry'):
                self.track_entry.delete(0, tk.END)
            # reset cover art info
            self.selected_cover_art = None
            self.remove_cover_art = False
            self.cover_art_filename.config(text="None")
            
            # Map EasyID3 keys to our field names
            field_map = {
                "Artist": "artist",
                "Title": "title",
                "Album": "album",
                "Genre": "genre",
                "Date": "date",
            }
            
            # Load values into text fields
            for field_name, id3_key in field_map.items():
                if id3_key in audio:
                    value = audio[id3_key]
                    # EasyID3 returns lists, take first value
                    if isinstance(value, list) and len(value) > 0:
                        self.fields[field_name].insert(0, value[0])
            # track number
            if 'tracknumber' in audio:
                t = audio['tracknumber']
                if isinstance(t, list) and t:
                    self.track_entry.insert(0, t[0])
                else:
                    self.track_entry.insert(0, t)
            
            # attempt to read existing cover art (APIC frame)
            try:
                id3 = ID3(file_path)
                pics = id3.getall("APIC")
                if pics:
                    # just show that art exists; we can't point to a real file
                    self.cover_art_filename.config(text="<embedded>")
                else:
                    self.cover_art_filename.config(text="None")
            except Exception:
                # ignore errors reading APIC
                pass

            self.set_status(f"Loaded: {os.path.basename(file_path)}", fg="green")

            # Autopopulate from folder structure
            file_path = self.folder_files[self.current_file_index] if self.folder_files else self.current_file

            if file_path:
                # Split the path into folders
                path_parts = file_path.replace("\\", "/").split("/")
                
                # Title = filename without extension
                # Only auto-populate if the field is currently empty so that any
                # user-edited title is preserved.  (Users were complaining that
                # changing a wrong Youtube title would be stomped by the
                # filename whenever metadata was reloaded.)
                filename = os.path.splitext(os.path.basename(file_path))[0]
                if not self.fields["Title"].get().strip():
                    self.fields["Title"].delete(0, tk.END)
                    self.fields["Title"].insert(0, filename)
                
                # Album = last folder
                if len(path_parts) >= 2 and not self.fields["Album"].get().strip():
                    self.fields["Album"].delete(0, tk.END)
                    self.fields["Album"].insert(0, path_parts[-2])
                
                # Artist = second-to-last folder
                if len(path_parts) >= 3 and not self.fields["Artist"].get().strip():
                    self.fields["Artist"].delete(0, tk.END)
                    self.fields["Artist"].insert(0, path_parts[-3])

            # Auto-lookup release date from MusicBrainz
            try:
                import musicbrainzngs
                musicbrainzngs.set_useragent("MediaTools", "1.0")
                
                artist_name = self.fields["Artist"].get()
                album_name = self.fields["Album"].get()
                
                if artist_name and album_name:
                    # Search for the release
                    results = musicbrainzngs.search_releases(
                        artist=artist_name,
                        release=album_name,
                        limit=1
                    )
                    
                    if results['release-list']:
                        release = results['release-list'][0]
                        
                        # Get release date
                        if 'date' in release:
                            self.fields["Date"].delete(0, tk.END)
                            self.fields["Date"].insert(0, release['date'][:4])  # Year only
                    
            except Exception as e:
                # Silently fail if lookup doesn't work
                pass
        
        except Exception as e:
            self.set_status(f"Error loading metadata: {str(e)}", fg="red")
    
    def apply_all_files(self):
        """Save only genre + cover art to all files"""
        allowed = {"Genre"}  # Only update genre for all files

        if self.folder_files:
            self._do_save(self.folder_files, allowed_fields=allowed)
        elif self.current_file:
            self._do_save([self.current_file], allowed_fields=allowed)
        else:
            self.set_status("No file/folder selected", fg="red")

    # def apply_all_files(self):
    #     """Save to all files (or just current if single file mode)"""
    #     if self.folder_files:
    #         self._do_save(self.folder_files)
    #     elif self.current_file:
    #         self._do_save([self.current_file])
    #     else:
    #         self.set_status("No file/folder selected", fg="red")
    
    def apply_current_file(self):
        """Save all fields to current file only"""
        allowed = {"Artist", "Title", "Album", "Genre", "Date"}

        if self.folder_files:
            self._do_save([self.folder_files[self.current_file_index]], allowed_fields=allowed)
        elif self.current_file:
            self._do_save([self.current_file], allowed_fields=allowed)
        else:
            self.set_status("No file/folder selected", fg="red")

    # def apply_current_file(self):
    #     """Save to current file only"""
    #     if self.folder_files:
    #         self._do_save([self.folder_files[self.current_file_index]])
    #     elif self.current_file:
    #         self._do_save([self.current_file])
    #     else:
    #         self.set_status("No file/folder selected", fg="red")
    
    # def _do_save(self, files_to_update):
    #     """Internal method that performs the actual save to given files"""
    #     try:
    #         # Map fields to ID3 keys
    #         field_map = {
    #             "Artist": "artist",
    #             "Title": "title",
    #             "Album": "album",
    #             "Genre": "genre",
    #             "Date": "date",
    #         }
            
    #         saved_count = 0
    #         for file_path in files_to_update:
    #             # Reload audio object for each file
    #             audio = EasyID3(file_path)
                
    #             # Update values
    #             for field_name, id3_key in field_map.items():
    #                 value = self.fields[field_name].get().strip()
    #                 if value:
    #                     audio[id3_key] = value
    #             # track number
    #             if hasattr(self, 'track_entry'):
    #                 tn = self.track_entry.get().strip()
    #                 if tn:
    #                     audio['tracknumber'] = tn
    #             # Save text tag changes
    #             audio.save()

    #             # now handle cover art / APIC
    #             try:
    #                 id3 = ID3(file_path)
    #                 if self.remove_cover_art:
    #                     id3.delall("APIC")
    #                 elif self.selected_cover_art:
    #                     with open(self.selected_cover_art, "rb") as img:
    #                         imgdata = img.read()
    #                     # clear old art then add new
    #                     id3.delall("APIC")
    #                     # choose mime type based on extension
    #                     mime = "image/jpeg"
    #                     if self.selected_cover_art.lower().endswith(".png"):
    #                         mime = "image/png"
    #                     id3.add(APIC(encoding=3,
    #                                  mime=mime,
    #                                  type=3,
    #                                  desc="Cover",
    #                                  data=imgdata))
    #                 id3.save(v2_version=3)
    #             except Exception:
    #                 # if something goes wrong with APIC, ignore and continue
    #                 pass

    #             saved_count += 1
            
    #         if saved_count == 1:
    #             self.set_status(f"Saved metadata to 1 file", fg="green")
    #         else:
    #             self.set_status(f"Saved metadata to {saved_count} files", fg="green")
        
    #     except Exception as e:
    #         self.set_status(f"Error saving metadata: {str(e)}", fg="red")

    def _do_save(self, files_to_update, allowed_fields=None):
        """Internal method that performs the actual save to given files"""
        try:
            if allowed_fields is None:
                allowed_fields = set()

            # Map fields to ID3 keys
            field_map = {
                "Artist": "artist",
                "Title": "title",
                "Album": "album",
                "Genre": "genre",
                "Date": "date",
            }

            saved_count = 0

            for file_path in files_to_update:
                audio = EasyID3(file_path)

                # Update only allowed fields
                for field_name, id3_key in field_map.items():
                    if field_name not in allowed_fields:
                        continue

                    value = self.fields[field_name].get().strip()
                    if value:
                        audio[id3_key] = value

                # Track number only applies when editing a single file
                if "Title" in allowed_fields and hasattr(self, 'track_entry'):
                    tn = self.track_entry.get().strip()
                    if tn:
                        audio['tracknumber'] = tn

                audio.save()

                # Handle cover art (always allowed)
                try:
                    id3 = ID3(file_path)

                    if self.remove_cover_art:
                        id3.delall("APIC")

                    elif self.selected_cover_art:
                        with open(self.selected_cover_art, "rb") as img:
                            imgdata = img.read()

                        id3.delall("APIC")

                        mime = "image/jpeg"
                        if self.selected_cover_art.lower().endswith(".png"):
                            mime = "image/png"

                        id3.add(APIC(
                            encoding=3,
                            mime=mime,
                            type=3,
                            desc="Cover",
                            data=imgdata
                        ))

                    id3.save(v2_version=3)

                except Exception:
                    pass

                saved_count += 1

            if saved_count == 1:
                self.set_status("Saved metadata to 1 file", fg="green")
            else:
                self.set_status(f"Saved metadata to {saved_count} files", fg="green")

        except Exception as e:
            self.set_status(f"Error saving metadata: {str(e)}", fg="red")

    def _apply_cover_to_files(self, files_to_update, cover_path):
        """Apply *only* the specified cover image to the given files.

        This helper is used by ``select_folder`` when the user chooses to
        automatically propagate a ``folder.jpg``; it avoids touching any of
        the other metadata fields (title/artist/track number/etc) which would
        otherwise be overwritten by :meth:`_do_save`.
        """
        try:
            applied = 0
            for file_path in files_to_update:
                try:
                    id3 = ID3(file_path)
                    # read image data
                    with open(cover_path, "rb") as img:
                        imgdata = img.read()
                    # clear existing artwork and add new
                    id3.delall("APIC")
                    mime = "image/jpeg"
                    if cover_path.lower().endswith(".png"):
                        mime = "image/png"
                    id3.add(APIC(encoding=3,
                                 mime=mime,
                                 type=3,
                                 desc="Cover",
                                 data=imgdata))
                    id3.save(v2_version=3)
                    applied += 1
                except Exception:
                    # ignore failures on individual files
                    continue
            self.set_status(f"Applied cover art to {applied} files", fg="green")
        except Exception as e:
            self.set_status(f"Error applying cover art: {str(e)}", fg="red")
