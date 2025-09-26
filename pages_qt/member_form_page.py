# pages_qt/member_form_page.py
# GymPro — Member Form (PyQt6). Create/Edit member details

from __future__ import annotations

from typing import Optional, Dict, Any

try:
    from router import PALETTE as SHARED_PALETTE  # type: ignore
except Exception:
    SHARED_PALETTE = None

PALETTE = SHARED_PALETTE or {
    "bg":       "#0f1218",
    "surface":  "#151a22",
    "card":     "#1b2130",
    "card2":    "#1e2636",
    "accent":   "#4f8cff",
    "muted":    "#8b93a7",
    "text":     "#e8ecf5",
}

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QLineEdit,
    QComboBox,
)


def _label(text: str, *, color: str | None = None, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    lbl.setStyleSheet(f"color:{color or PALETTE['text']}; font-family:'Segoe UI'; font-size:13px; font-weight:{weight};")
    return lbl


class SectionCard(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self.setStyleSheet(f"QFrame#SectionCard {{ background-color: {PALETTE['card']}; border-radius: 16px; }}")
        lay = QVBoxLayout(self); lay.setContentsMargins(16,14,16,12); lay.setSpacing(8)
        lay.addWidget(_label(title, bold=True))


class MemberFormPage(QWidget):
    def __init__(self, member: Optional[Dict[str, Any]] = None, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.member = member or {}

        self.setObjectName("MemberFormPage")
        self.setStyleSheet(
            f"""
            QWidget#MemberFormPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{ background: {PALETTE['card2']}; color: {PALETTE['text']}; selection-background-color: {PALETTE['accent']}; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:32px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:32px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.setColumnStretch(0, 1); root.setRowStretch(1, 1)

        card = SectionCard("Member Details")
        form = QFrame(); fg = QGridLayout(form); fg.setContentsMargins(12,8,12,8); fg.setHorizontalSpacing(8)
        labels = ["First Name", "Last Name", "Phone", "UID", "Status", "Notes"]
        self.ent_fn = QLineEdit(); self.ent_ln = QLineEdit(); self.ent_ph = QLineEdit(); self.ent_uid = QLineEdit()
        self.opt_status = QComboBox(); self.opt_status.addItems(["Active","Suspended","Expired","Blacklisted"]) 
        self.ent_notes = QLineEdit()
        fields = [self.ent_fn, self.ent_ln, self.ent_ph, self.ent_uid, self.opt_status, self.ent_notes]
        for i, lab in enumerate(labels):
            fg.addWidget(_label(lab, color=PALETTE['muted']), i, 0)
            fg.addWidget(fields[i], i, 1)
        btns = QFrame(); hb = QHBoxLayout(btns); hb.setContentsMargins(0,0,0,0)
        b_cancel = QPushButton("Cancel"); b_cancel.setProperty("cssClass","secondary")
        b_save = QPushButton("Save"); b_save.setProperty("cssClass","primary"); b_save.clicked.connect(self._save)
        hb.addWidget(b_cancel); hb.addWidget(b_save)
        fg.addWidget(btns, len(labels), 0, 1, 2, alignment=Qt.AlignmentFlag.AlignRight)
        card.layout().addWidget(form)  # type: ignore
        root.addWidget(card, 0, 0)

        self._prefill()

    def _prefill(self):
        self.ent_fn.setText(str(self.member.get('first_name','')))
        self.ent_ln.setText(str(self.member.get('last_name','')))
        self.ent_ph.setText(str(self.member.get('phone','')))
        self.ent_uid.setText(str(self.member.get('uid','')))
        st = str(self.member.get('status','Active')).capitalize()
        if st in [self.opt_status.itemText(i) for i in range(self.opt_status.count())]:
            self.opt_status.setCurrentText(st)
        self.ent_notes.setText(str(self.member.get('notes','')))

    def _save(self):
        data = {
            'first_name': (self.ent_fn.text() or '').strip(),
            'last_name': (self.ent_ln.text() or '').strip(),
            'phone': (self.ent_ph.text() or '').strip(),
            'uid': (self.ent_uid.text() or '').strip(),
            'status': self.opt_status.currentText(),
            'notes': (self.ent_notes.text() or '').strip(),
        }
        if self.services and hasattr(self.services, 'save_member'):
            try: self.services.save_member(data)
            except Exception: pass
        print('Saved member:', data)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    root = QWidget(); root.setObjectName('Root'); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(900, 600)
    page = MemberFormPage(member=None, services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
