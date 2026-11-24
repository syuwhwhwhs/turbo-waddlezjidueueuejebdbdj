import os, sqlite3
from app.config import DATABASE_PATH

def db():
    os.makedirs(os.path.dirname(DATABASE_PATH) or '.', exist_ok=True)
    c=sqlite3.connect(DATABASE_PATH, timeout=30)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(
          user_id INTEGER PRIMARY KEY, language TEXT NOT NULL DEFAULT 'fa',
          first_name TEXT DEFAULT '', username TEXT DEFAULT '',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS jobs(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          emoji_id TEXT NOT NULL, mode TEXT NOT NULL, replacement TEXT NOT NULL,
          source_file_id TEXT NOT NULL, source_format TEXT NOT NULL,
          status TEXT DEFAULT 'queued', result_path TEXT, pack_name TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(user_id));
        CREATE TABLE IF NOT EXISTS user_packs(
          user_id INTEGER PRIMARY KEY, pack_name TEXT NOT NULL, title TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(user_id));
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status,id);
        CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id,id);
        ''')
        # Safe forward migrations for databases created by earlier builds.
        cols={r['name'] for r in c.execute('PRAGMA table_info(jobs)')}
        if 'result_path' not in cols: c.execute('ALTER TABLE jobs ADD COLUMN result_path TEXT')
        if 'pack_name' not in cols: c.execute('ALTER TABLE jobs ADD COLUMN pack_name TEXT')
        c.execute("UPDATE jobs SET status='queued' WHERE status='processing'")

def user(uid):
    with db() as c:
        r=c.execute('SELECT * FROM users WHERE user_id=?',(uid,)).fetchone()
        return dict(r) if r else None

def save(uid,lang=None,name='',username=''):
    old=user(uid)
    language=lang or (old['language'] if old else 'fa')
    with db() as c:
        c.execute('''INSERT INTO users(user_id,language,first_name,username) VALUES(?,?,?,?)
          ON CONFLICT(user_id) DO UPDATE SET language=excluded.language,
          first_name=excluded.first_name,username=excluded.username''',
          (uid,language,name,username))
    return language

def get_job(jid):
    with db() as c:
        r=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        return dict(r) if r else None


def get_user_pack(uid):
    with db() as c:
        r=c.execute('SELECT * FROM user_packs WHERE user_id=?',(uid,)).fetchone()
        return dict(r) if r else None

def save_user_pack(uid,name,title):
    with db() as c:
        c.execute('INSERT INTO user_packs(user_id,pack_name,title) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET pack_name=excluded.pack_name,title=excluded.title',(uid,name,title))
