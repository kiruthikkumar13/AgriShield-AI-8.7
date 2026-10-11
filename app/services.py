"""Business logic for accounts, marketplace, bulk deals and service network."""
import datetime

from . import auth
from .errors import ApiError
from .knowledge import DISTRICTS, ROLES


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")


def _txt(d, k, req=True, mx=200):
    v = str(d.get(k) or "").strip()
    if req and not v:
        raise ApiError(400, "%s is required" % k)
    if len(v) > mx:
        raise ApiError(400, "%s is too long" % k)
    return v


def _num(d, k):
    try:
        v = float(d.get(k))
    except (TypeError, ValueError):
        raise ApiError(400, "%s must be a number" % k)
    if not (0 < v < 1e9):
        raise ApiError(400, "%s must be positive" % k)
    return v


def _int(d, k):
    try:
        return int(d.get(k))
    except (TypeError, ValueError):
        raise ApiError(400, "%s must be an id" % k)


def need(u, *roles):
    if not u or u["role"] not in roles:
        raise ApiError(403, "This action needs role: " + " / ".join(roles))


def _pub(u):
    return {k: u[k] for k in ("id", "name", "email", "role", "phone", "district")}


def register(db, d):
    name, email = _txt(d, "name", mx=80), _txt(d, "email", mx=120).lower()
    pw, role = str(d.get("password") or ""), d.get("role")
    if "@" not in email or len(pw) < 6 or role not in ROLES:
        raise ApiError(400, "Valid email, password (6+ chars) and role are required")
    district = _txt(d, "district", False, 60)
    if district and district not in DISTRICTS:
        raise ApiError(400, "Unknown district")
    if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
        raise ApiError(409, "Email already registered")
    salt, h = auth.hash_pw(pw)
    cur = db.execute("INSERT INTO users(name,email,salt,pw,role,phone,district) VALUES(?,?,?,?,?,?,?)",
                     (name, email, salt, h, role, _txt(d, "phone", False, 20), district))
    u = db.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return {"token": auth.make_token(u["id"], role), "user": _pub(u)}


def login(db, d):
    u = db.execute("SELECT * FROM users WHERE email=?", (_txt(d, "email").lower(),)).fetchone()
    if not u or not auth.check_pw(str(d.get("password") or ""), u["salt"], u["pw"]):
        raise ApiError(401, "Wrong email or password")
    return {"token": auth.make_token(u["id"], u["role"]), "user": _pub(u)}


def user_from_token(db, token):
    data = auth.read_token(token or "")
    u = data and db.execute("SELECT * FROM users WHERE id=?", (data["uid"],)).fetchone()
    if not u:
        raise ApiError(401, "Please log in")
    return u


# ---- marketplace ----
def create_listing(db, u, d):
    need(u, "farmer")
    cur = db.execute("INSERT INTO listings(farmer_id,crop,qty_kg,price_kg,district,note,created) VALUES(?,?,?,?,?,?,?)",
                     (u["id"], _txt(d, "crop", mx=40).lower(), _num(d, "qty_kg"), _num(d, "price_kg"),
                      _txt(d, "district", False, 60) or u["district"] or "", _txt(d, "note", False, 200), _now()))
    return {"id": cur.lastrowid}


def list_listings(db, crop="", district="", mine_for=None):
    q = "SELECT l.*, u.name AS farmer FROM listings l JOIN users u ON u.id=l.farmer_id WHERE 1=1"
    a = []
    if mine_for:
        q += " AND l.farmer_id=?"
        a.append(mine_for)
    else:
        q += " AND l.status='active' AND l.qty_kg>0"
    if crop:
        q += " AND l.crop=?"
        a.append(crop.lower())
    if district:
        q += " AND l.district=?"
        a.append(district)
    return [dict(r) for r in db.execute(q + " ORDER BY l.id DESC LIMIT 100", a)]


def place_order(db, u, d):
    need(u, "consumer", "bulk_buyer")
    qty = _num(d, "qty_kg")
    l = db.execute("SELECT * FROM listings WHERE id=? AND status='active'", (_int(d, "listing_id"),)).fetchone()
    if not l:
        raise ApiError(404, "Listing not found")
    if qty > l["qty_kg"]:
        raise ApiError(400, "Only %.1f kg available" % l["qty_kg"])
    left = l["qty_kg"] - qty
    db.execute("UPDATE listings SET qty_kg=?, status=? WHERE id=?", (left, "active" if left > 0 else "sold", l["id"]))
    cur = db.execute("INSERT INTO orders(listing_id,buyer_id,qty_kg,total,status,created) VALUES(?,?,?,?,?,?)",
                     (l["id"], u["id"], qty, round(qty * l["price_kg"], 2), "placed", _now()))
    return {"id": cur.lastrowid, "total": round(qty * l["price_kg"], 2)}


def my_orders(db, u):
    base = ("SELECT o.*, l.crop, l.price_kg, f.name AS farmer, b.name AS buyer FROM orders o JOIN listings l ON l.id=o.listing_id "
            "JOIN users f ON f.id=l.farmer_id JOIN users b ON b.id=o.buyer_id WHERE ")
    return {"placed": [dict(r) for r in db.execute(base + "o.buyer_id=? ORDER BY o.id DESC", (u["id"],))],
            "incoming": [dict(r) for r in db.execute(base + "l.farmer_id=? ORDER BY o.id DESC", (u["id"],))]}


def update_order(db, u, oid, status):
    o = db.execute("SELECT o.*, l.farmer_id FROM orders o JOIN listings l ON l.id=o.listing_id WHERE o.id=?", (oid,)).fetchone()
    if not o:
        raise ApiError(404, "Order not found")
    farmer, buyer = o["farmer_id"] == u["id"], o["buyer_id"] == u["id"]
    ok = {("placed", "accepted"): farmer, ("placed", "cancelled"): farmer or buyer,
          ("accepted", "delivered"): farmer, ("accepted", "cancelled"): farmer}
    if not (farmer or buyer):
        raise ApiError(403, "Not your order")
    if not ok.get((o["status"], status)):
        raise ApiError(400, "Cannot change order from %s to %s" % (o["status"], status))
    if status == "cancelled":
        db.execute("UPDATE listings SET qty_kg=qty_kg+?, status='active' WHERE id=?", (o["qty_kg"], o["listing_id"]))
    db.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    return {"id": oid, "status": status}


# ---- bulk requests / offers ----
def create_request(db, u, d):
    need(u, "bulk_buyer")
    cur = db.execute("INSERT INTO requests(buyer_id,crop,qty_kg,target_kg,district,created) VALUES(?,?,?,?,?,?)",
                     (u["id"], _txt(d, "crop", mx=40).lower(), _num(d, "qty_kg"), _num(d, "target_kg"),
                      _txt(d, "district", False, 60), _now()))
    return {"id": cur.lastrowid}


def list_requests(db, u):
    rows = db.execute("SELECT r.*, b.name AS buyer, (SELECT COUNT(*) FROM offers o WHERE o.request_id=r.id) AS offers "
                      "FROM requests r JOIN users b ON b.id=r.buyer_id WHERE r.status='open' OR r.buyer_id=? ORDER BY r.id DESC LIMIT 100", (u["id"],))
    return [dict(r) for r in rows]


def make_offer(db, u, d):
    need(u, "farmer")
    r = db.execute("SELECT * FROM requests WHERE id=? AND status='open'", (_int(d, "request_id"),)).fetchone()
    if not r:
        raise ApiError(404, "Open request not found")
    cur = db.execute("INSERT INTO offers(request_id,farmer_id,price_kg,qty_kg,created) VALUES(?,?,?,?,?)",
                     (r["id"], u["id"], _num(d, "price_kg"), _num(d, "qty_kg"), _now()))
    return {"id": cur.lastrowid}


def request_offers(db, u, rid):
    r = db.execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone()
    if not r or r["buyer_id"] != u["id"]:
        raise ApiError(404, "Request not found")
    return [dict(o) for o in db.execute("SELECT o.*, f.name AS farmer FROM offers o JOIN users f ON f.id=o.farmer_id WHERE o.request_id=? ORDER BY o.price_kg", (rid,))]


def accept_offer(db, u, oid):
    o = db.execute("SELECT o.*, r.buyer_id, r.status AS rstatus FROM offers o JOIN requests r ON r.id=o.request_id WHERE o.id=?", (oid,)).fetchone()
    if not o or o["buyer_id"] != u["id"]:
        raise ApiError(404, "Offer not found")
    if o["rstatus"] != "open" or o["status"] != "pending":
        raise ApiError(400, "Offer can no longer be accepted")
    db.execute("UPDATE offers SET status='rejected' WHERE request_id=? AND id<>?", (o["request_id"], oid))
    db.execute("UPDATE offers SET status='accepted' WHERE id=?", (oid,))
    db.execute("UPDATE requests SET status='closed' WHERE id=?", (o["request_id"],))
    return {"deal": {"offer_id": oid, "price_kg": o["price_kg"], "qty_kg": o["qty_kg"], "total": round(o["price_kg"] * o["qty_kg"], 2)}}


# ---- service network ----
def add_service(db, u, d):
    need(u, "service_provider")
    cur = db.execute("INSERT INTO services(provider_id,kind,note,district) VALUES(?,?,?,?)",
                     (u["id"], _txt(d, "kind", mx=60), _txt(d, "note", False, 200), _txt(d, "district", False, 60) or u["district"] or ""))
    return {"id": cur.lastrowid}


def list_services(db, district=""):
    q, a = "SELECT s.*, u.name AS provider, u.phone FROM services s JOIN users u ON u.id=s.provider_id", []
    if district:
        q, a = q + " WHERE s.district=?", [district]
    return [dict(r) for r in db.execute(q + " ORDER BY s.id DESC LIMIT 100", a)]


def request_service(db, u, d):
    need(u, "farmer")
    if not db.execute("SELECT 1 FROM services WHERE id=?", (_int(d, "service_id"),)).fetchone():
        raise ApiError(404, "Service not found")
    cur = db.execute("INSERT INTO service_requests(service_id,farmer_id,note,created) VALUES(?,?,?,?)",
                     (_int(d, "service_id"), u["id"], _txt(d, "note", False, 200), _now()))
    return {"id": cur.lastrowid}


def my_service_requests(db, u):
    q = ("SELECT r.*, s.kind, f.name AS farmer, f.phone FROM service_requests r JOIN services s ON s.id=r.service_id "
         "JOIN users f ON f.id=r.farmer_id WHERE %s ORDER BY r.id DESC")
    return [dict(r) for r in db.execute(q % ("s.provider_id=?" if u["role"] == "service_provider" else "r.farmer_id=?"), (u["id"],))]


def update_service_request(db, u, rid, status):
    need(u, "service_provider")
    r = db.execute("SELECT r.* FROM service_requests r JOIN services s ON s.id=r.service_id WHERE r.id=? AND s.provider_id=?", (rid, u["id"])).fetchone()
    if not r:
        raise ApiError(404, "Request not found")
    if status not in ("accepted", "done", "declined"):
        raise ApiError(400, "Invalid status")
    db.execute("UPDATE service_requests SET status=? WHERE id=?", (status, rid))
    return {"id": rid, "status": status}


# ---- scan history ----
def save_scan(db, u, crop, result):
    top = result["matches"][0]["name"] if result["matches"] else "healthy"
    db.execute("INSERT INTO scans(user_id,crop,summary,created) VALUES(?,?,?,?)",
               (u["id"], crop, "%s (%s%% affected, %s)" % (top, result["affected_pct"], result["severity"]), _now()))


def list_scans(db, u):
    return [dict(r) for r in db.execute("SELECT * FROM scans WHERE user_id=? ORDER BY id DESC LIMIT 20", (u["id"],))]
