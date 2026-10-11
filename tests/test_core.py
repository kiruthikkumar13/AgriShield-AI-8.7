import io, unittest

from PIL import Image, ImageDraw

from app import engine, services as S
from app.auth import make_token, read_token
from app.db import connect
from app.errors import ApiError
from app.seed import seed


def leaf(spots=0, color=(120, 70, 30)):
    im = Image.new("RGB", (200, 200), (40, 140, 50))
    d = ImageDraw.Draw(im)
    for i in range(spots):
        x, y = 20 + (i % 5) * 36, 20 + (i // 5) * 36
        d.ellipse([x, y, x + 24, y + 24], fill=color)
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def user(db, email, role, district="Coimbatore"):
    S.register(db, dict(name=role, email=email, password="secret1", role=role, district=district))
    return db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()


class Engine(unittest.TestCase):
    def test_recommend_district_and_inputs(self):
        r = engine.recommend(None, None, "kharif", 2, "Thanjavur")
        self.assertEqual(r["soil"], "alluvial")
        self.assertIn("paddy", [x["crop"] for x in r["results"]])
        r = engine.recommend("red", "low", "kharif", 1)
        names = [x["crop"] for x in r["results"]]
        self.assertIn("ragi", names)
        self.assertNotIn("paddy", names)
        with self.assertRaises(ApiError):
            engine.recommend("moon", "low", "kharif")

    def test_economics(self):
        e = engine.economics("tomato", 2)
        self.assertEqual(e["cost"], 120000)
        self.assertLess(e["profit_pessimistic"], e["profit_optimistic"])
        self.assertEqual(engine.economics("tomato", 1, 2000)["price"], 2000)
        for bad in (("tomato", 0), ("nope", 1), ("tomato", 1, -5)):
            with self.assertRaises(ApiError):
                engine.economics(*bad)

    def test_intercrop_layout(self):
        r = engine.intercrop_layout("coconut", "turmeric", 30, 30)
        self.assertEqual(r["main_count"], 16)
        self.assertGreater(r["partner_count"], 0)
        self.assertTrue(all(0 <= p[0] <= 30 and 0 <= p[1] <= 30 for p in r["main_points"]))
        self.assertTrue(all(0 < row["y"] < 30 for row in r["partner_rows"]))
        for bad in (("coconut", "paddy", 30, 30), ("paddy", "onion", 30, 30), ("coconut", "onion", 5, 5)):
            with self.assertRaises(ApiError):
                engine.intercrop_layout(*bad)

    def test_market(self):
        m = engine.market("tomato")
        self.assertEqual(len(m["monthly"]), 12)
        self.assertEqual(len(m["best_months"]), 3)

    def test_detect(self):
        h = engine.detect(leaf(0), "tomato")
        self.assertEqual(h["status"], "healthy")
        d = engine.detect(leaf(15), "tomato", ["brown spots"])
        self.assertEqual(d["status"], "possible_issue")
        self.assertIn("early_blight", [m["id"] for m in d["matches"]])
        self.assertGreater(d["affected_pct"], 5)
        with self.assertRaises(ApiError):
            engine.detect(b"not an image", "tomato")


class Services(unittest.TestCase):
    def setUp(self):
        self.db = connect(":memory:")

    def test_auth(self):
        r = S.register(self.db, dict(name="A", email="A@x.com", password="secret1", role="farmer"))
        self.assertEqual(read_token(r["token"])["uid"], r["user"]["id"])
        self.assertIsNone(read_token(r["token"] + "x"))
        self.assertEqual(S.login(self.db, dict(email="a@x.com", password="secret1"))["user"]["role"], "farmer")
        for bad in (dict(name="A", email="a@x.com", password="secret1", role="farmer"), dict(name="B", email="b", password="secret1", role="farmer"),
                    dict(name="B", email="b@x.com", password="1", role="farmer"), dict(name="B", email="b@x.com", password="secret1", role="boss")):
            with self.assertRaises(ApiError):
                S.register(self.db, bad)
        with self.assertRaises(ApiError) as c:
            S.login(self.db, dict(email="a@x.com", password="wrong"))
        self.assertEqual(c.exception.status, 401)
        with self.assertRaises(ApiError):
            S.user_from_token(self.db, "garbage")

    def test_order_flow(self):
        f, b = user(self.db, "f@x.com", "farmer"), user(self.db, "c@x.com", "consumer")
        lid = S.create_listing(self.db, f, dict(crop="Tomato", qty_kg=50, price_kg=20))["id"]
        with self.assertRaises(ApiError):
            S.create_listing(self.db, b, dict(crop="tomato", qty_kg=5, price_kg=1))
        o = S.place_order(self.db, b, dict(listing_id=lid, qty_kg=30))
        self.assertEqual(o["total"], 600)
        with self.assertRaises(ApiError):
            S.place_order(self.db, b, dict(listing_id=lid, qty_kg=30))
        self.assertEqual(S.list_listings(self.db)[0]["qty_kg"], 20)
        S.update_order(self.db, f, o["id"], "accepted")
        with self.assertRaises(ApiError):
            S.update_order(self.db, b, o["id"], "delivered")
        S.update_order(self.db, f, o["id"], "cancelled")
        self.assertEqual(S.list_listings(self.db)[0]["qty_kg"], 50)
        self.assertEqual(len(S.my_orders(self.db, f)["incoming"]), 1)
        self.assertEqual(S.my_orders(self.db, b)["placed"][0]["status"], "cancelled")

    def test_bulk_deal(self):
        f, f2, bb = user(self.db, "f@x.com", "farmer"), user(self.db, "f2@x.com", "farmer"), user(self.db, "b@x.com", "bulk_buyer")
        rid = S.create_request(self.db, bb, dict(crop="onion", qty_kg=1000, target_kg=25))["id"]
        o1 = S.make_offer(self.db, f, dict(request_id=rid, price_kg=24, qty_kg=600))["id"]
        S.make_offer(self.db, f2, dict(request_id=rid, price_kg=26, qty_kg=500))
        self.assertEqual(len(S.request_offers(self.db, bb, rid)), 2)
        with self.assertRaises(ApiError):
            S.accept_offer(self.db, f, o1)
        self.assertEqual(S.accept_offer(self.db, bb, o1)["deal"]["total"], 14400)
        with self.assertRaises(ApiError):
            S.make_offer(self.db, f2, dict(request_id=rid, price_kg=20, qty_kg=1))
        self.assertEqual(S.list_requests(self.db, bb)[0]["status"], "closed")

    def test_services_and_seed(self):
        seed(self.db)
        self.assertEqual(len(S.list_services(self.db, "Coimbatore")), 1)
        f = self.db.execute("SELECT * FROM users WHERE email='farmer@demo.com'").fetchone()
        p = self.db.execute("SELECT * FROM users WHERE email='expert@demo.com'").fetchone()
        rid = S.request_service(self.db, f, dict(service_id=1, note="Soil test"))["id"]
        self.assertEqual(len(S.my_service_requests(self.db, p)), 1)
        S.update_service_request(self.db, p, rid, "accepted")
        with self.assertRaises(ApiError):
            S.update_service_request(self.db, f, rid, "done")
        seed(self.db)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 4)
        res = engine.detect(leaf(15), "tomato", [])
        S.save_scan(self.db, f, "tomato", res)
        self.assertEqual(len(S.list_scans(self.db, f)), 1)


if __name__ == "__main__":
    unittest.main()
