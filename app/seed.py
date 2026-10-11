from . import services as S


def seed(db):
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return
    mk = lambda n, e, r, d, p="9000000000": S.register(db, dict(name=n, email=e, password="demo123", role=r, district=d, phone=p))["user"]
    farmer = mk("Demo Farmer", "farmer@demo.com", "farmer", "Coimbatore")
    mk("Demo Consumer", "consumer@demo.com", "consumer", "Coimbatore")
    mk("Demo Wholesaler", "buyer@demo.com", "bulk_buyer", "Erode")
    prov = mk("Demo Agri Expert", "expert@demo.com", "service_provider", "Coimbatore")
    f = db.execute("SELECT * FROM users WHERE id=?", (farmer["id"],)).fetchone()
    p = db.execute("SELECT * FROM users WHERE id=?", (prov["id"],)).fetchone()
    for crop, q, pr in (("tomato", 200, 22), ("onion", 500, 28), ("turmeric", 100, 90)):
        S.create_listing(db, f, dict(crop=crop, qty_kg=q, price_kg=pr, district="Coimbatore", note="Fresh from farm (sample data)"))
    S.add_service(db, p, dict(kind="Crop advisory visit", note="Field visit and soil test help (sample)", district="Coimbatore"))
    db.commit()
