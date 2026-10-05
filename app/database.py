import json, sqlite3
from pathlib import Path
class Database:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.conn=sqlite3.connect(self.path); self.conn.row_factory=sqlite3.Row
        self.conn.executescript("""CREATE TABLE IF NOT EXISTS commands(
        id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,category TEXT NOT NULL,
        platform TEXT NOT NULL,shell TEXT NOT NULL,command TEXT NOT NULL,description TEXT NOT NULL,
        tags TEXT DEFAULT '',safety TEXT DEFAULT 'Safe',kind TEXT DEFAULT 'command',
        steps TEXT DEFAULT '[]',favorite INTEGER DEFAULT 0,use_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_title ON commands(title);
        CREATE INDEX IF NOT EXISTS idx_category ON commands(category);""")
    def count(self): return self.conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    def seed(self,path):
        if self.count(): return
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        self.conn.executemany("INSERT INTO commands(title,category,platform,shell,command,description,tags,safety,kind,steps) VALUES(?,?,?,?,?,?,?,?,?,?)",
            [(x["title"],x["category"],x["platform"],x["shell"],x["command"],x["description"],x["tags"],x["safety"],x["kind"],json.dumps(x["steps"])) for x in data])
        self.conn.commit()
    def categories(self): return self.conn.execute("SELECT category,COUNT(*) n FROM commands GROUP BY category ORDER BY category").fetchall()
    def search(self,text="",category="All",favorites=False):
        q=f"%{text}%"
        return self.conn.execute("""SELECT * FROM commands WHERE
        (?='' OR title LIKE ? OR description LIKE ? OR command LIKE ? OR tags LIKE ?)
        AND (?='All' OR category=?) AND (?=0 OR favorite=1)
        ORDER BY favorite DESC,use_count DESC,title""",(text,q,q,q,q,category,category,int(favorites))).fetchall()
    def get(self,cid): return self.conn.execute("SELECT * FROM commands WHERE id=?",(cid,)).fetchone()
    def increment(self,cid): self.conn.execute("UPDATE commands SET use_count=use_count+1 WHERE id=?",(cid,)); self.conn.commit()
    def toggle_favorite(self,cid): self.conn.execute("UPDATE commands SET favorite=1-favorite WHERE id=?",(cid,)); self.conn.commit()
    def close(self): self.conn.close()
