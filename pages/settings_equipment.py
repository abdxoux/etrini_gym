# /pages/settings_equipment.py
# GymPro — Settings: Gym Equipment & Maintenance (UI-only)
from __future__ import annotations
import csv, datetime as dt
from typing import Any, Dict, List, Optional
import customtkinter as ctk
from tkinter import filedialog, messagebox

PALETTE={"bg":"#0f1218","surface":"#151a22","card":"#1b2130","card2":"#1e2636",
         "accent":"#4f8cff","muted":"#8b93a7","text":"#e8ecf5","warn":"#f59e0b","danger":"#ef4444"}

class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title:str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"], font=("Segoe UI Semibold",15)).grid(row=0,column=0,sticky="w",padx=16,pady=(14,8))

class EquipTable(ctk.CTkScrollableFrame):
    COLS=("Name","Category","Serial","Status","Last service","Notes")
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        hdr=ctk.CTkFrame(self, fg_color="transparent"); hdr.pack(fill="x", padx=8, pady=(0,4))
        for i,t in enumerate(self.COLS):
            ctk.CTkLabel(hdr, text=t, text_color=PALETTE["muted"]).grid(row=0,column=i, padx=(12 if i==0 else 8,8), sticky="w")
        self._rows=[]; self._data=[]
    def set_rows(self, rows:List[Dict[str,Any]]):
        for w in self._rows: w.destroy()
        self._rows.clear(); self._data=rows
        for i,r in enumerate(rows):
            row=ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=10); row.pack(fill="x", padx=8, pady=6)
            vals=(r["name"], r["category"], r["serial"], r["status"], r["last_service"], r.get("notes",""))
            for j,v in enumerate(vals):
                ctk.CTkLabel(row, text=str(v), text_color=PALETTE["text"] if j in (0,3) else PALETTE["muted"]).grid(row=0,column=j, padx=(12 if j==0 else 8,8), pady=8, sticky="w")
            self._rows.append(row)
    def export_csv(self, path:str):
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(self.COLS)
            for r in self._data: w.writerow([r["name"], r["category"], r["serial"], r["status"], r["last_service"], r.get("notes","")])

class MaintTable(ctk.CTkScrollableFrame):
    COLS=("Time","Equipment","Issue","Action","Technician","Status")
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        hdr=ctk.CTkFrame(self, fg_color="transparent"); hdr.pack(fill="x", padx=8, pady=(0,4))
        for i,t in enumerate(self.COLS):
            ctk.CTkLabel(hdr, text=t, text_color=PALETTE["muted"]).grid(row=0,column=i, padx=(12 if i==0 else 8,8), sticky="w")
        self._rows=[]; self._data=[]
    def set_rows(self, rows:List[Dict[str,Any]]):
        for w in self._rows: w.destroy()
        self._rows.clear(); self._data=rows
        for i,r in enumerate(rows):
            row=ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=10); row.pack(fill="x", padx=8, pady=6)
            vals=(r["time"][:16], r["equip"], r["issue"], r["action"], r["tech"], r["status"])
            for j,v in enumerate(vals):
                ctk.CTkLabel(row, text=str(v), text_color=PALETTE["text"] if j in (0,1,5) else PALETTE["muted"]).grid(row=0,column=j, padx=(12 if j==0 else 8,8), pady=8, sticky="w")
            self._rows.append(row)
    def export_csv(self, path:str):
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(self.COLS)
            for r in self._data: w.writerow([r["time"], r["equip"], r["issue"], r["action"], r["tech"], r["status"]])

class SettingsEquipmentPage(ctk.CTkFrame):
    """
    services.equipment.list(q, cat) -> list of equipment
    services.equipment.maintenance(from,to,q) -> list of logs
    services.equipment.add_issue(equip_id, issue) -> None
    """
    def __init__(self, master, services: Optional[object]=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services=services
        self.grid_columnconfigure(0, weight=2); self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)

        title=SectionCard(self,"Settings — Equipment & Maintenance")
        title.grid(row=0,column=0,columnspan=2, sticky="ew", padx=16, pady=(16,8))

        # LEFT — equipment
        left=ctk.CTkFrame(self, fg_color="transparent"); left.grid(row=1,column=0,rowspan=2, sticky="nsew", padx=(16,8), pady=(8,16))
        left.grid_rowconfigure(2, weight=1)

        filt=SectionCard(left,"Equipment — Filters")
        filt.grid(row=0,column=0, sticky="ew"); filt.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(filt, text="Search", text_color=PALETTE["muted"]).grid(row=1,column=0, padx=16, sticky="w")
        self.ent_q=ctk.CTkEntry(filt, placeholder_text="Name / serial"); self.ent_q.grid(row=1,column=1, sticky="ew", padx=(0,16), pady=8)
        self.ent_q.bind("<KeyRelease>", lambda e: self._refresh_equipment())

        eq=SectionCard(left,"Equipment")
        eq.grid(row=1,column=0, sticky="nsew", pady=(8,0))
        eq.grid_rowconfigure(1, weight=1)
        self.tbl_eq=EquipTable(eq); self.tbl_eq.grid(row=1,column=0, sticky="nsew", padx=8, pady=(0,10))
        # quick new issue
        quick=ctk.CTkFrame(eq, fg_color=PALETTE["card2"], corner_radius=12); quick.grid(row=2,column=0, sticky="ew", padx=8, pady=(0,10))
        quick.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(quick, text="Log issue for equipment (by name prefix):", text_color=PALETTE["muted"]).grid(row=0,column=0,padx=10,pady=8, sticky="w")
        self.ent_issue_name=ctk.CTkEntry(quick, placeholder_text="e.g., Treadmill"); self.ent_issue_name.grid(row=0,column=1, sticky="ew", padx=6)
        self.ent_issue=ctk.CTkEntry(quick, placeholder_text="Issue description"); self.ent_issue.grid(row=0,column=2, padx=6)
        ctk.CTkButton(quick, text="Add", fg_color=PALETTE["accent"], hover_color="#3e74d6", command=self._add_issue).grid(row=0,column=3, padx=6)

        # RIGHT — maintenance
        right=ctk.CTkFrame(self, fg_color="transparent"); right.grid(row=1,column=1,rowspan=2, sticky="nsew", padx=(8,16), pady=(8,16))
        right.grid_rowconfigure(1, weight=1)

        mf=SectionCard(right,"Maintenance Log — Filters / Export")
        mf.grid(row=0,column=0, sticky="ew"); mf.grid_columnconfigure(1, weight=1)
        today=dt.date.today().isoformat()
        ctk.CTkLabel(mf, text="From", text_color=PALETTE["muted"]).grid(row=1,column=0,padx=16, sticky="w")
        self.ent_from=ctk.CTkEntry(mf); self.ent_from.insert(0,today); self.ent_from.grid(row=1,column=1, sticky="ew", padx=(0,16), pady=6)
        ctk.CTkLabel(mf, text="To", text_color=PALETTE["muted"]).grid(row=1,column=2,padx=16, sticky="w")
        self.ent_to=ctk.CTkEntry(mf); self.ent_to.insert(0,today); self.ent_to.grid(row=1,column=3, sticky="ew", padx=(0,16), pady=6)
        ctk.CTkLabel(mf, text="Search", text_color=PALETTE["muted"]).grid(row=1,column=4,padx=16, sticky="w")
        self.ent_qm=ctk.CTkEntry(mf, placeholder_text="Equipment / issue / tech"); self.ent_qm.grid(row=1,column=5, sticky="ew", padx=(0,16), pady=6)
        ctk.CTkButton(mf, text="Refresh", fg_color="#2a3550", hover_color="#334066", command=self._refresh_maint).grid(row=1,column=6,padx=10)
        ctk.CTkButton(mf, text="Export CSV", fg_color="#263042", hover_color="#32405a", command=self._export_maint).grid(row=1,column=7,padx=(0,12))

        mt=SectionCard(right,"Maintenance Log")
        mt.grid(row=1,column=0, sticky="nsew", pady=(8,0))
        mt.grid_rowconfigure(1, weight=1)
        self.tbl_mt=MaintTable(mt); self.tbl_mt.grid(row=1,column=0, sticky="nsew", padx=8, pady=(0,10))

        # seed + render
        self._mock_data(); self._refresh_equipment(); self._refresh_maint()

    # --- actions / mocks ---
    def _refresh_equipment(self):
        q=(self.ent_q.get() or "").lower().strip()
        rows=[e for e in self._equip if (not q or q in e["name"].lower() or q in e["serial"].lower())]
        self.tbl_eq.set_rows(rows)

    def _add_issue(self):
        name=(self.ent_issue_name.get() or "").strip().lower()
        issue=(self.ent_issue.get() or "").strip()
        if not name or not issue: return
        eq=next((e for e in self._equip if e["name"].lower().startswith(name)), None)
        if not eq:
            messagebox.showwarning("Equipment","Not found"); return
        rec={"time":dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "equip":eq["name"], "issue":issue,
             "action":"—","tech":"—","status":"open"}
        self._maint.insert(0,rec); self._refresh_maint()
        self.ent_issue_name.delete(0,"end"); self.ent_issue.delete(0,"end")

    def _refresh_maint(self):
        q=(self.ent_qm.get() or "").lower().strip()
        d1=self.ent_from.get().strip(); d2=self.ent_to.get().strip()
        rows=[m for m in self._maint if (m["time"][:10]>=d1 and m["time"][:10]<=d2)
              and (not q or q in m["equip"].lower() or q in m["issue"].lower() or q in m["tech"].lower())]
        self.tbl_mt.set_rows(rows)

    def _export_maint(self):
        path=filedialog.asksaveasfilename(title="Export Maintenance", defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        self.tbl_mt.export_csv(path); messagebox.showinfo("Export", f"Saved to:\n{path}")

    def _mock_data(self):
        self._equip=[
            {"name":"Treadmill A","category":"Cardio","serial":"TR-001","status":"OK","last_service":"2025-08-10","notes":""},
            {"name":"Elliptical B","category":"Cardio","serial":"EL-112","status":"OK","last_service":"2025-07-05","notes":""},
            {"name":"Bench Press","category":"Strength","serial":"BP-220","status":"Needs pads","last_service":"2025-06-12","notes":""},
            {"name":"Cable Machine","category":"Strength","serial":"CB-019","status":"OK","last_service":"2025-07-28","notes":""},
        ]
        now=dt.datetime.now()
        def rec(mins, equip, issue, action, tech, status):
            return {"time":(now-dt.timedelta(minutes=mins)).strftime("%Y-%m-%d %H:%M"),
                    "equip":equip,"issue":issue,"action":action,"tech":tech,"status":status}
        self._maint=[
            rec(15,"Treadmill A","Belt squeak","Lubed belt","R. Tech","closed"),
            rec(210,"Bench Press","Loose bolt","Tightened","R. Tech","closed"),
            rec(600,"Elliptical B","Display flicker","—","—","open"),
        ]

if __name__=="__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root=ctk.CTk(); root.geometry("1400x900"); root.configure(fg_color=PALETTE["bg"])
    page=SettingsEquipmentPage(root); page.pack(fill="both", expand=True); root.mainloop()
