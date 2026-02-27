"""
pages/register_mp_page.py - MP Register Page (Member/Personnel)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os

from pages.base_page import BasePage
from config import COLORS, PHOTOS_DIR, PHOTO_CONFIG


class RegisterMPPage(BasePage):
    """Member/Personnel registration page"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.photo_refs = {}  # Menyimpan referensi foto agar tidak di-garbage collect
        self._create_widgets()
    
    def _create_widgets(self):
        """Membuat widget"""
        # Header
        self.create_header("👥 Register MP", "Member / Personnel Registration")
        
        # Control section
        self._create_control_section()
        
        # Member list section
        self._create_member_list_section()
    
    def _create_control_section(self):
        """Section kontrol"""
        control_frame = tk.Frame(self, bg=self.colors["bg_card"])
        control_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        inner = tk.Frame(control_frame, bg=self.colors["bg_card"])
        inner.pack(fill="x", padx=20, pady=15)
        
        # Tombol tambah
        tk.Button(
            inner, text="➕ Add Member",
            font=("Segoe UI", 11),
            bg=self.colors["accent_green"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=20, pady=10,
            command=self._show_add_dialog
        ).pack(side="left", padx=5)
        
        # Search
        tk.Label(
            inner, text="🔍 Search:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(30, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._filter_members())
        
        search_entry = tk.Entry(
            inner,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat", width=25
        )
        search_entry.pack(side="left", padx=5, ipady=6)
        
        # Stats
        self.stats_label = tk.Label(
            inner,
            text="Total: 0 members",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        )
        self.stats_label.pack(side="right", padx=10)
    
    def _create_member_list_section(self):
        """Section daftar member"""
        section = tk.Frame(self, bg=self.colors["bg_card"])
        section.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Canvas dengan scrollbar
        self.canvas = tk.Canvas(section, bg=self.colors["bg_card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=self.canvas.yview)
        self.member_frame = tk.Frame(self.canvas, bg=self.colors["bg_card"])
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.member_frame, anchor="nw")
        
        def configure_scroll(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Adjust width
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        self.member_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", configure_scroll)
        
        # Mouse wheel
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    
    def _load_members(self, filter_text=""):
        """Load dan tampilkan daftar member"""
        # Clear existing
        for widget in self.member_frame.winfo_children():
            widget.destroy()
        self.photo_refs = {}
        
        members = self.controller.data_manager.mp_register.get("members", [])
        
        # Filter
        if filter_text:
            filter_text = filter_text.lower()
            members = [m for m in members if 
                      filter_text in m["id_number"].lower() or 
                      filter_text in m["name"].lower()]
        
        # Update stats
        total = len(self.controller.data_manager.mp_register.get("members", []))
        shown = len(members)
        self.stats_label.configure(text=f"Total: {total} members" + (f" (Showing: {shown})" if filter_text else ""))
        
        # Header
        header_frame = tk.Frame(self.member_frame, bg=self.colors["bg_active"])
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        headers = [("No", 50), ("ID Number", 120), ("Name", 250), ("Photo", 100), ("Registered", 150), ("Action", 120)]
        for text, width in headers:
            tk.Label(
                header_frame, text=text,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_active"],
                fg=self.colors["text_primary"],
                width=width // 8,
                pady=10
            ).pack(side="left", padx=2)
        
        # Members
        if not members:
            tk.Label(
                self.member_frame,
                text="📭 No members registered yet",
                font=("Segoe UI", 14),
                bg=self.colors["bg_card"],
                fg=self.colors["text_secondary"],
                pady=50
            ).pack()
            return
        
        for idx, member in enumerate(members):
            self._create_member_row(idx, member)
    
    def _create_member_row(self, idx, member):
        """Membuat baris member"""
        bg = self.colors["bg_hover"] if idx % 2 == 0 else self.colors["bg_card"]
        
        row_frame = tk.Frame(self.member_frame, bg=bg)
        row_frame.pack(fill="x", padx=10, pady=2)
        
        # No
        tk.Label(
            row_frame, text=str(idx + 1),
            font=("Segoe UI", 10),
            bg=bg, fg=self.colors["text_primary"],
            width=6, pady=10
        ).pack(side="left", padx=2)
        
        # ID Number
        tk.Label(
            row_frame, text=member["id_number"],
            font=("Segoe UI", 10, "bold"),
            bg=bg, fg=self.colors["accent"],
            width=15, anchor="w"
        ).pack(side="left", padx=2)
        
        # Nama
        tk.Label(
            row_frame, text=member["name"],
            font=("Segoe UI", 10),
            bg=bg, fg=self.colors["text_primary"],
            width=30, anchor="w"
        ).pack(side="left", padx=2)
        
        # Foto
        photo_frame = tk.Frame(row_frame, bg=bg, width=80, height=60)
        photo_frame.pack(side="left", padx=5)
        photo_frame.pack_propagate(False)
        
        if member.get("photo"):
            photo_path = self.controller.data_manager.get_photo_path(member["photo"])
            if photo_path and os.path.exists(photo_path):
                try:
                    img = Image.open(photo_path)
                    img.thumbnail((60, 60))
                    photo = ImageTk.PhotoImage(img)
                    self.photo_refs[member["id_number"]] = photo
                    
                    tk.Label(
                        photo_frame, image=photo,
                        bg=bg
                    ).pack(expand=True)
                except:
                    tk.Label(
                        photo_frame, text="👤",
                        font=("Segoe UI", 20),
                        bg=bg, fg=self.colors["text_secondary"]
                    ).pack(expand=True)
            else:
                tk.Label(
                    photo_frame, text="👤",
                    font=("Segoe UI", 20),
                    bg=bg, fg=self.colors["text_secondary"]
                ).pack(expand=True)
        else:
            tk.Label(
                photo_frame, text="👤",
                font=("Segoe UI", 20),
                bg=bg, fg=self.colors["text_secondary"]
            ).pack(expand=True)
        
        # Terdaftar
        created = member.get("created_at", "N/A")
        tk.Label(
            row_frame, text=created[:10] if len(created) > 10 else created,
            font=("Segoe UI", 9),
            bg=bg, fg=self.colors["text_secondary"],
            width=18
        ).pack(side="left", padx=2)
        
        # Aksi
        action_frame = tk.Frame(row_frame, bg=bg)
        action_frame.pack(side="left", padx=5)
        
        tk.Button(
            action_frame, text="✏️",
            font=("Segoe UI", 9),
            bg=self.colors["accent"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda m=member: self._show_edit_dialog(m)
        ).pack(side="left", padx=2)
        
        tk.Button(
            action_frame, text="🗑️",
            font=("Segoe UI", 9),
            bg=self.colors["accent_red"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda m=member: self._delete_member(m)
        ).pack(side="left", padx=2)
    
    def _show_add_dialog(self):
        """Tampilkan dialog tambah member"""
        dialog = MemberDialog(self, self.controller, mode="add")
        self.wait_window(dialog)
        
        if dialog.result:
            self._load_members()
    
    def _show_edit_dialog(self, member):
        """Tampilkan dialog edit member"""
        dialog = MemberDialog(self, self.controller, mode="edit", member=member)
        self.wait_window(dialog)
        
        if dialog.result:
            self._load_members()
    
    def _delete_member(self, member):
        """Hapus member"""
        if messagebox.askyesno("Konfirmasi", 
                               f"Hapus member?\n\nID: {member['id_number']}\nNama: {member['name']}"):
            success, msg = self.controller.data_manager.delete_member(member["id_number"])
            if success:
                self._load_members()
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", msg)
    
    def _filter_members(self):
        """Filter member berdasarkan pencarian"""
        self._load_members(self.search_var.get())
    
    def on_show(self):
        """Called when page is shown"""
        self._load_members()


class MemberDialog(tk.Toplevel):
    """Dialog untuk tambah/edit member"""
    
    def __init__(self, parent, controller, mode="add", member=None):
        super().__init__(parent)
        
        self.controller = controller
        self.mode = mode
        self.member = member
        self.result = False
        self.selected_photo = None
        self.photo_preview = None
        
        self.title("➕ Add Member" if mode == "add" else "✏️ Edit Member")
        self.geometry("450x500")
        self.configure(bg=COLORS["bg_card"])
        
        self._create_widgets()
        
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        """Membuat widget dialog"""
        # Header
        tk.Label(
            self,
            text="➕ Add New Member" if self.mode == "add" else "✏️ Edit Member",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]
        ).pack(pady=20)
        
        # Form
        form_frame = tk.Frame(self, bg=COLORS["bg_card"])
        form_frame.pack(fill="both", expand=True, padx=30)
        
        # ID Number
        row1 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=10)
        
        tk.Label(
            row1, text="ID Number:",
            font=("Segoe UI", 11),
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            width=12, anchor="w"
        ).pack(side="left")
        
        self.id_entry = tk.Entry(
            row1,
            font=("Segoe UI", 11),
            bg=COLORS["bg_hover"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat", width=25
        )
        self.id_entry.pack(side="left", ipady=6)
        
        if self.member:
            self.id_entry.insert(0, self.member["id_number"])
            if self.mode == "edit":
                self.id_entry.configure(state="disabled")
        
        # Nama
        row2 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=10)
        
        tk.Label(
            width=12, anchor="w"
        ).pack(side="left")
        
        self.name_entry = tk.Entry(
            row2,
            font=("Segoe UI", 11),
            bg=COLORS["bg_hover"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat", width=25
        )
        self.name_entry.pack(side="left", ipady=6)
        
        if self.member:
            self.name_entry.insert(0, self.member["name"])
        
        # Foto
        row3 = tk.Frame(form_frame, bg=COLORS["bg_card"])
        row3.pack(fill="x", pady=10)
        
        tk.Label(
            row3, text="Photo:",
            font=("Segoe UI", 11),
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            width=12, anchor="w"
        ).pack(side="left")
        
        tk.Button(
            row3, text="📷 Select Photo",
            font=("Segoe UI", 10),
            bg=COLORS["accent"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=15,
            command=self._select_photo
        ).pack(side="left")
        
        self.photo_label = tk.Label(
            row3, text="None selected",
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]
        )
        self.photo_label.pack(side="left", padx=10)
        
        # Photo preview
        self.preview_frame = tk.Frame(form_frame, bg=COLORS["bg_hover"], width=150, height=150)
        self.preview_frame.pack(pady=20)
        self.preview_frame.pack_propagate(False)
        
        # Load existing photo for edit mode
        if self.member and self.member.get("photo"):
            photo_path = self.controller.data_manager.get_photo_path(self.member["photo"])
            if photo_path and os.path.exists(photo_path):
                self._show_photo_preview(photo_path)
        else:
            tk.Label(
                self.preview_frame, text="👤\nPhoto Preview",
                font=("Segoe UI", 14),
                bg=COLORS["bg_hover"],
                fg=COLORS["text_secondary"]
            ).pack(expand=True)
        
        # Buttons
        btn_frame = tk.Frame(self, bg=COLORS["bg_card"])
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame, text="💾 Save",
            font=("Segoe UI", 11),
            bg=COLORS["accent_green"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=25, pady=10,
            command=self._save
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame, text="❌ Cancel",
            font=("Segoe UI", 11),
            bg=COLORS["accent_red"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=25, pady=10,
            command=self.destroy
        ).pack(side="left", padx=10)
    
    def _select_photo(self):
        """Pilih foto"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("All files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=filetypes
        )
        
        if filepath:
            self.selected_photo = filepath
            filename = os.path.basename(filepath)
            self.photo_label.configure(text=filename[:20] + "..." if len(filename) > 20 else filename)
            self._show_photo_preview(filepath)
    
    def _show_photo_preview(self, filepath):
        """Tampilkan preview foto"""
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        try:
            img = Image.open(filepath)
            img.thumbnail((140, 140))
            self.photo_preview = ImageTk.PhotoImage(img)
            
            tk.Label(
                self.preview_frame, image=self.photo_preview,
                bg=COLORS["bg_hover"]
            ).pack(expand=True)
        except Exception as e:
            tk.Label(
                self.preview_frame, text="❌\nFailed to load photo",
                font=("Segoe UI", 10),
                bg=COLORS["bg_hover"],
                fg=COLORS["accent_red"]
            ).pack(expand=True)
    
    def _save(self):
        """Simpan member"""
        id_number = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        
        if not id_number:
            messagebox.showerror("Error", "ID Number must be filled!")
            return
        
        if not name:
            messagebox.showerror("Error", "Name must be filled!")
            return
        
        dm = self.controller.data_manager
        
        if self.mode == "add":
            success, msg = dm.add_member(id_number, name, self.selected_photo)
        else:
            success, msg = dm.update_member(id_number, name, self.selected_photo)
        
        if success:
            self.result = True
            messagebox.showinfo("Success", msg)
            self.destroy()
        else:
            messagebox.showerror("Error", msg)