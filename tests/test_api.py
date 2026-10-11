"""HTTP-level tests. Need: pip install -r requirements-dev.txt (skipped if FastAPI/httpx missing)."""
import os, tempfile, unittest

try:
    os.environ["AGRISHIELD_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
    from fastapi.testclient import TestClient
    from app.main import app
    from tests.test_core import leaf
except ImportError:
    app = None


@unittest.skipIf(app is None, "FastAPI/httpx not installed")
class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cm = TestClient(app)
        cls.c = cls.cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.cm.__exit__(None, None, None)

    def hdr(self, email="farmer@demo.com"):
        t = self.c.post("/api/login", json={"email": email, "password": "demo123"}).json()["token"]
        return {"Authorization": "Bearer " + t}

    def test_public(self):
        self.assertTrue(self.c.get("/health").json()["ok"])
        self.assertIn("paddy", self.c.get("/api/meta").json()["crops"])
        r = self.c.post("/api/recommend", json={"district": "Thanjavur", "season": "kharif", "acres": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.post("/api/recommend", json={"season": "x"}).status_code, 400)
        self.assertEqual(self.c.post("/api/economics", json={"crop": "tomato", "acres": 2}).json()["cost"], 120000)
        r = self.c.post("/api/intercrop", json={"main": "coconut", "partner": "turmeric", "width": 30, "length": 30})
        self.assertEqual(r.json()["main_count"], 16)
        self.assertEqual(len(self.c.get("/api/market", params={"crop": "onion"}).json()["monthly"]), 12)
        self.assertGreaterEqual(len(self.c.get("/api/listings").json()), 3)
        self.assertEqual(self.c.get("/").status_code, 200)

    def test_detect_and_auth(self):
        files = {"image": ("leaf.png", leaf(15), "image/png")}
        r = self.c.post("/api/detect", files=files, data={"crop": "tomato", "symptoms": "brown spots"}, headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.post("/api/detect", data={"crop": "tomato"}).status_code, 400)
        self.assertEqual(len(self.c.get("/api/scans", headers=self.hdr()).json()), 1)
        self.assertEqual(self.c.get("/api/orders").status_code, 401)

    def test_market_flow(self):
        fh, ch = self.hdr(), self.hdr("consumer@demo.com")
        lid = self.c.get("/api/listings").json()[0]["id"]
        r = self.c.post("/api/orders", json={"listing_id": lid, "qty_kg": 1}, headers=ch)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.post("/api/orders", json={"listing_id": lid, "qty_kg": 1}, headers=fh).status_code, 403)
        oid = r.json()["id"]
        self.assertEqual(self.c.post("/api/orders/%d/status" % oid, json={"status": "accepted"}, headers=fh).status_code, 200)
        bh = self.hdr("buyer@demo.com")
        rid = self.c.post("/api/requests", json={"crop": "onion", "qty_kg": 100, "target_kg": 20}, headers=bh).json()["id"]
        oid = self.c.post("/api/offers", json={"request_id": rid, "price_kg": 19, "qty_kg": 100}, headers=fh).json()["id"]
        self.assertEqual(self.c.post("/api/offers/%d/accept" % oid, headers=bh).json()["deal"]["total"], 1900)
