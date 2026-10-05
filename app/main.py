import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.database import Database
from app.ui.main_window import MainWindow
BASE=Path(__file__).resolve().parent.parent
db=Database(BASE/'jass_command_vault.db'); db.seed(BASE/'data/default_commands.json')
app=QApplication(sys.argv); w=MainWindow(db); w.show(); code=app.exec(); db.close(); sys.exit(code)
