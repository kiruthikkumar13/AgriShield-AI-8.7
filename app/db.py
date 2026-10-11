import os, pathlib, sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, salt TEXT, pw TEXT, role TEXT, phone TEXT, district TEXT);
CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY, farmer_id INTEGER REFERENCES users(id), crop TEXT, qty_kg REAL, price_kg REAL, district TEXT, note TEXT, status TEXT DEFAULT 'active', created TEXT);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, listing_id INTEGER REFERENCES listings(id), buyer_id INTEGER REFERENCES users(id), qty_kg REAL, total REAL, status TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, buyer_id INTEGER REFERENCES users(id), crop TEXT, qty_kg REAL, target_kg REAL, district TEXT, status TEXT DEFAULT 'open', created TEXT);
CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY, request_id INTEGER REFERENCES requests(id), farmer_id INTEGER REFERENCES users(id), price_kg REAL, qty_kg REAL, status TEXT DEFAULT 'pending', created TEXT);
CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, provider_id INTEGER REFERENCES users(id), kind TEXT, note TEXT, district TEXT);
CREATE TABLE IF NOT EXISTS service_requests(id INTEGER PRIMARY KEY, service_id INTEGER REFERENCES services(id), farmer_id INTEGER REFERENCES users(id), note TEXT, status TEXT DEFAULT 'open', created TEXT);
CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), crop TEXT, summary TEXT, created TEXT);
"""


def connect(path=None):
    path = path or os.environ.get("AGRISHIELD_DB") or str(ROOT / "data" / "agrishield.db")
    if path != ":memory:":
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn
