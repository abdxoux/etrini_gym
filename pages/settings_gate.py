# /pages/settings_gate.py
# GymPro — Settings: Gate TCP/IP (UI-only)
from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

PALETTE={"bg":"#0f1218","surface":"#151a22","card":"#1b2130","card2":"#1e2636",
         "accent":"#4f8cff","muted":"#8b93a7","text":"#e8ecf5","ok":"#22c55e","danger":"#ef4444"}

class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title:str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"], font=("Segoe UI Semibold",15)).grid(row=0,column=0,sticky="w",padx=16,pady=(14,8))

class SettingsGatePage(ctk.CTkFrame):
    """
    services.gate.test(ip, port, timeout) -> bool
    services.gate.save(ip, port, open_cmd, close_cmd) -> None
    services.gate.open() / close()
    """
    def __init__(self, master, services: Optional[object]=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services=services
        self.grid_columnconfigure(0, weight=1)
        title=SectionCard(self,"Settings — Gate TCP/IP"); title.grid(row=0,column=0, sticky="ew", padx=16, pady=(16,8))

        card=SectionCard(self,"Configuration"); card.grid(row=1,column=0, sticky="ew", padx=16, pady=(8,16))
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card,text="IP Address", text_color=PALETTE["text"]).grid(row=1,column=0,padx=16,pady=6,sticky="w")
        self.ent_ip=ctk.CTkEntry(card, placeholder_text="e.g., 192.168.1.10"); self.ent_ip.grid(row=1,column=1, sticky="ew", padx=(0,16))
        ctk.CTkLabel(card,text="Port", text_color=PALETTE["text"]).grid(row=2,column=0,padx=16,pady=6,sticky="w")
        self.ent_port=ctk.CTkEntry(card, placeholder_text="e.g., 5000"); self.ent_port.grid(row=2,column=1, sticky="w", padx=(0,16))
        ctk.CTkLabel(card,text="Open Command", text_color=PALETTE["text"]).grid(row=3,column=0,padx=16,pady=6,sticky="w")
        self.ent_open=ctk.CTkEntry(card, placeholder_text="hex or ascii"); self.ent_open.grid(row=3,column=1, sticky="ew", padx=(0,16))
        ctk.CTkLabel(card,text="Close Command", text_color=PALETTE["text"]).grid(row=4,column=0,padx=16,pady=6,sticky="w")
        self.ent_close=ctk.CTkEntry(card, placeholder_text="hex or ascii"); self.ent_close.grid(row=4,column=1, sticky="ew", padx=(0,16))

        btns=ctk.CTkFrame(card, fg_color="transparent"); btns.grid(row=5,column=0,columnspan=2, sticky="e", padx=16, pady=(8,12))
        ctk.CTkButton(btns, text="Test", fg_color="#2a3550", hover_color="#334066", command=self._test).pack(side="left")
        ctk.CTkButton(btns, text="Save", fg_color=PALETTE["accent"], hover_color="#3e74d6", command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Open Gate", fg_color="#20321f", hover_color="#234625", command=self._open_gate).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Close Gate", fg_color="#3a1418", hover_color="#4a1c22", command=self._close_gate).pack(side="left")

    def _test(self):
        ok = getattr(getattr(self.services,"gate",None),"test", lambda *_: True)(self.ent_ip.get(), int(self.ent_port.get() or 0), 1000)
        messagebox.showinfo("Gate", "Connection OK." if ok else "Connection failed.")

    def _save(self):
        try:
            getattr(getattr(self.services,"gate",None),"save", lambda *args, **kw: None)(
                self.ent_ip.get(), int(self.ent_port.get() or 0), self.ent_open.get(), self.ent_close.get()
            )
            messagebox.showinfo("Gate","Saved.")
        except Exception as e:
            messagebox.showerror("Gate", str(e))

    def _open_gate(self):
        try:
            getattr(getattr(self.services,"gate",None),"open", lambda: None)(); messagebox.showinfo("Gate","Open command sent.")
        except Exception as e:
            messagebox.showerror("Gate", str(e))

    def _close_gate(self):
        try:
            getattr(getattr(self.services,"gate",None),"close", lambda: None)(); messagebox.showinfo("Gate","Close command sent.")
        except Exception as e:
            messagebox.showerror("Gate", str(e))

if __name__=="__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root=ctk.CTk(); root.geometry("900x520"); root.configure(fg_color=PALETTE["bg"])
    page=SettingsGatePage(root); page.pack(fill="both", expand=True); root.mainloop()
