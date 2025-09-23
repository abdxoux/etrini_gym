# /pages/settings_language.py
# GymPro — Settings: Language (UI-only)
from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

PALETTE={"bg":"#0f1218","surface":"#151a22","card":"#1b2130","card2":"#1e2636",
         "accent":"#4f8cff","muted":"#8b93a7","text":"#e8ecf5"}

class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title:str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"], font=("Segoe UI Semibold",15)).grid(row=0,column=0,sticky="w",padx=16,pady=(14,8))

class SettingsLanguagePage(ctk.CTkFrame):
    """
    services.settings.get_language() -> 'en'|'fr'|'ar'
    services.settings.set_language(code) -> None
    """
    def __init__(self, master, services: Optional[object]=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services=services
        self.grid_columnconfigure(0, weight=1)
        title=SectionCard(self,"Settings — Language"); title.grid(row=0,column=0, sticky="ew", padx=16, pady=(16,8))

        card=SectionCard(self,"Choose Language"); card.grid(row=1,column=0, sticky="ew", padx=16, pady=(8,16))
        ctk.CTkLabel(card, text="App Language", text_color=PALETTE["text"]).grid(row=1,column=0, padx=16, pady=8, sticky="w")
        self.opt_lang=ctk.CTkOptionMenu(card, values=["en","fr","ar"], width=120); self.opt_lang.grid(row=1,column=1, padx=8, pady=8)
        ctk.CTkButton(card, text="Save", fg_color=PALETTE["accent"], hover_color="#3e74d6", command=self._save).grid(row=1,column=2, padx=8, pady=8)

        self._load()

    def _load(self):
        cur=getattr(getattr(self.services,"settings",None),"get_language", lambda:"en")()
        self.opt_lang.set(cur)

    def _save(self):
        code=self.opt_lang.get()
        try:
            getattr(getattr(self.services,"settings",None),"set_language", lambda *_:None)(code)
            messagebox.showinfo("Language","Saved. Restart app to apply.")
        except Exception as e:
            messagebox.showerror("Language", str(e))

if __name__=="__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root=ctk.CTk(); root.geometry("700x300"); root.configure(fg_color=PALETTE["bg"])
    page=SettingsLanguagePage(root); page.pack(fill="both", expand=True); root.mainloop()
