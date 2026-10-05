import os,re,json,subprocess
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QListWidget,QListWidgetItem,QLabel,QTextEdit,QPushButton,QComboBox,QCheckBox,QSplitter,QMessageBox,QInputDialog,QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
def substitute(s,parent):
    vals={}
    for name in sorted(set(re.findall(r"\{([A-Z0-9_]+)\}",s))):
        v,ok=QInputDialog.getText(parent,"Command variable",f"Value for {{{name}}}:")
        if not ok:return None
        vals[name]=v
    for k,v in vals.items(): s=s.replace("{"+k+"}",v)
    return s
class MainWindow(QMainWindow):
    def __init__(self,db):
        super().__init__(); self.db=db; self.current=None
        self.setWindowTitle("JASS Command Vault V2"); self.resize(1250,780); self.build(); self.refresh()
    def build(self):
        w=QWidget(); self.setCentralWidget(w); root=QVBoxLayout(w); top=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("Search commands, recipes, tags or descriptions..."); self.search.textChanged.connect(self.refresh)
        self.cat=QComboBox(); self.cat.currentTextChanged.connect(self.refresh)
        self.fav=QCheckBox("★ Favorites"); self.fav.stateChanged.connect(self.refresh)
        top.addWidget(QLabel("🔎")); top.addWidget(self.search,1); top.addWidget(self.cat); top.addWidget(self.fav); root.addLayout(top)
        split=QSplitter(); self.list=QListWidget(); self.list.currentItemChanged.connect(self.show_item); split.addWidget(self.list)
        panel=QWidget(); p=QVBoxLayout(panel)
        self.title=QLabel("Select a command"); self.title.setFont(QFont("Segoe UI",16,QFont.Bold))
        self.meta=QLabel(""); self.desc=QLabel(""); self.desc.setWordWrap(True)
        self.code=QTextEdit(); self.code.setReadOnly(True); self.code.setFont(QFont("Consolas",11))
        self.steps=QTextEdit(); self.steps.setReadOnly(True); self.steps.setMaximumHeight(170)
        buttons=QHBoxLayout()
        for txt,fn in [("COPY",self.copy),("RUN",self.run),("★ FAVORITE",self.favorite)]:
            b=QPushButton(txt); b.clicked.connect(fn); buttons.addWidget(b)
        p.addWidget(self.title); p.addWidget(self.meta); p.addWidget(self.desc); p.addWidget(QLabel("COMMAND / RECIPE")); p.addWidget(self.code,1); p.addWidget(QLabel("RECIPE STEPS")); p.addWidget(self.steps); p.addLayout(buttons)
        split.addWidget(panel); split.setSizes([410,840]); root.addWidget(split,1)
        self.status=QLabel(); root.addWidget(self.status)
    def refresh(self):
        cats=["All"]+[r["category"] for r in self.db.categories()]; old=self.cat.currentText()
        self.cat.blockSignals(True); self.cat.clear(); self.cat.addItems(cats); self.cat.setCurrentText(old if old in cats else "All"); self.cat.blockSignals(False)
        self.list.clear(); rows=self.db.search(self.search.text().strip(),self.cat.currentText(),self.fav.isChecked())
        for r in rows:
            it=QListWidgetItem(("★ " if r["favorite"] else "")+r["title"]+("  [RECIPE]" if r["kind"]=="recipe" else "")); it.setData(Qt.UserRole,r["id"]); self.list.addItem(it)
        self.status.setText(f"{len(rows)} matching • {self.db.count()} total entries")
    def show_item(self,cur,prev=None):
        if not cur:return
        r=self.db.get(cur.data(Qt.UserRole)); self.current=r
        self.title.setText(r["title"]); self.meta.setText(f"{r['category']} • {r['platform']} • {r['shell']} • {r['safety']} • {r['kind']}")
        self.desc.setText(r["description"]); self.code.setPlainText(r["command"])
        s=json.loads(r["steps"] or "[]"); self.steps.setPlainText("\n".join(f"{i+1}. {x}" for i,x in enumerate(s)) if s else "Single command")
    def copy(self):
        if not self.current:return
        r=self.current; txt="\n".join(json.loads(r["steps"] or "[]")) if r["kind"]=="recipe" else r["command"]
        QApplication.clipboard().setText(txt); self.db.increment(r["id"]); self.status.setText("Copied to clipboard")
    def favorite(self):
        if self.current:self.db.toggle_favorite(self.current["id"]); self.refresh()
    def run(self):
        if not self.current:return
        r=self.current
        if r["kind"]=="recipe": QMessageBox.information(self,"Recipe","Use COPY for the guided steps and run them one at a time."); return
        cmd=substitute(r["command"],self)
        if cmd is None:return
        if r["safety"]=="Destructive" and QMessageBox.warning(self,"Destructive command","This may delete or overwrite data. Continue?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        self.db.increment(r["id"])
        try:
            if os.name=="nt":
                if "powershell" in r["shell"].lower(): subprocess.Popen(["powershell","-NoExit","-Command",cmd])
                else: subprocess.Popen(["cmd","/k",cmd])
            else: subprocess.Popen(["x-terminal-emulator","-e","bash","-lc",cmd])
            self.status.setText("Command launched")
        except Exception as e: QMessageBox.critical(self,"Run failed",str(e))

