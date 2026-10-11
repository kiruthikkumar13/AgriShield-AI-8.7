# AgriShield AI — From Soil to Sale (working prototype)
Team Green Coders · FastAPI + SQLite + vanilla JS PWA (English / Tamil)

## Run (Python 3.10+)
```
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 — the app opens on a login screen (log in, register, or continue as guest). The SQLite database (`data/agrishield.db`) and demo data are created on first start.

Demo logins (password `demo123`): farmer@demo.com · consumer@demo.com · buyer@demo.com · expert@demo.com

## Tests
```
python -m unittest discover -s tests -v      # core + service tests (no web server needed)
pip install -r requirements-dev.txt          # then the same command also runs the HTTP API tests
```

## What is built
| Module | What it does |
|---|---|
| Crop Plan | Ranks 13 crops for district / soil / water / season with reasons and profit range |
| Economics | Cost, yield, revenue, profit range, cautious/optimistic case, break-even price |
| Intercrop planner | Compatible crop pairs, spacing rules, SVG top-down layout, plant counts, material cost |
| Protect | Leaf photo + symptoms → ranked possible issues, severity, treatment, prevention; scan history |
| Market | Seasonal price pattern and best selling months (sample data) |
| Marketplace | Farmer listings, consumer/bulk orders with stock + status flow, bulk requests, offers, deal acceptance |
| Services | Experts/technicians directory, service requests and status updates |
| Accounts | Register/login, 4 roles (farmer, consumer, bulk buyer, service provider), signed tokens, PBKDF2 passwords |
| PWA + language | Installable (manifest + service worker), Tamil / English toggle |

## Honest limitations (also stated in the app)
- Agronomy values (costs, yields, prices, spacings, disease rules) are **indicative sample data**. Validate with TNAU / ICAR / local agriculture officers.
- Disease screening is a **heuristic** (leaf colour analysis + reported symptoms), **not a trained ML model**. The planned upgrade is transfer learning (e.g. MobileNet) on PlantVillage, tested on unseen images.
- Market prices are a sample seasonal pattern, not live prices. No UPI payments yet (future scope). Offline-first is not implemented; only the app shell is cached.
- Set `AGRISHIELD_SECRET` (and use HTTPS) before any real deployment. No yield, profit or price is guaranteed.

## Layout
`app/knowledge.py` data · `app/engine.py` decision logic · `app/services.py` accounts/marketplace/services · `app/main.py` FastAPI routes · `static/` PWA front end · `tests/`
