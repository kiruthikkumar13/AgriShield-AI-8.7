"""Pure decision-support logic (no web/DB). Rule-based prototype -- estimates, not guarantees."""
import io
import math

from .errors import ApiError
from .knowledge import CROPS, DISEASES, DISTRICTS, INTERCROP, SEASONS, SOILS, WATER

NOTE = "Indicative estimates from sample data. Not a guarantee of yield, profit or prices; validate with local agriculture experts."
_W = {"low": 1, "medium": 2, "high": 3}


def _crop(name):
    if name not in CROPS:
        raise ApiError(400, "Unknown crop: %s" % name)
    return CROPS[name]


def economics(crop, acres=1.0, price=None):
    c = _crop(crop)
    acres = float(acres)
    if acres <= 0 or acres > 10000:
        raise ApiError(400, "Acres must be between 0 and 10000")
    price = float(price) if price not in (None, "") else c["price"]
    if price <= 0:
        raise ApiError(400, "Price must be positive")
    cost = c["cost"] * acres
    ylo, yhi = c["yield_"][0] * acres, c["yield_"][1] * acres
    ymid = (ylo + yhi) / 2
    return {"crop": crop, "acres": acres, "unit": c["unit"], "price": price, "cost": round(cost),
            "yield_range": [round(ylo, 1), round(yhi, 1)],
            "revenue_range": [round(ylo * price), round(yhi * price)],
            "profit_expected_range": [round(ylo * price - cost), round(yhi * price - cost)],
            "profit_pessimistic": round(ylo * price * 0.85 - cost),
            "profit_optimistic": round(yhi * price * 1.15 - cost),
            "break_even_price": round(cost / ymid, 1), "days": c["days"], "note": NOTE}


def recommend(soil=None, water=None, season=None, acres=1.0, district=None):
    if district:
        if district not in DISTRICTS:
            raise ApiError(400, "Unknown district")
        ds, dw = DISTRICTS[district]
        soil, water = soil or ds, water or dw
    if soil not in SOILS or water not in WATER or season not in SEASONS:
        raise ApiError(400, "Provide valid soil, water and season (or a district)")
    out = []
    for name, c in CROPS.items():
        score, why = 0, []
        if soil in c["soils"]:
            score += 3
            why.append("Suits %s soil" % soil)
        else:
            score -= 2
        if _W[c["water"]] <= _W[water]:
            score += 3
            why.append("Water need (%s) fits %s availability" % (c["water"], water))
        else:
            score -= 5
        if season in c["seasons"]:
            score += 3
            why.append("Grown in %s season" % season)
        elif "perennial" in c["seasons"]:
            score += 1
            why.append("Perennial crop")
        else:
            score -= 3
        if score >= 5:
            e = economics(name, acres)
            out.append({"crop": name, "ta": c["ta"], "score": score, "reasons": why, "days": c["days"],
                        "profit_range": e["profit_expected_range"], "unit": c["unit"]})
    out.sort(key=lambda r: (-r["score"], -r["profit_range"][1]))
    return {"soil": soil, "water": water, "season": season, "results": out[:5], "note": NOTE}


def intercrop_layout(main, partner, width, length):
    """Top-down layout. Main crop on a grid; partner rows run along the width in the inter-row gaps."""
    if main not in INTERCROP:
        raise ApiError(400, "No intercrop data for %s" % main)
    if partner not in INTERCROP[main]:
        raise ApiError(400, "%s is not a listed intercrop for %s" % (partner, main))
    W, L = float(width), float(length)
    if not (1 <= W <= 1000 and 1 <= L <= 1000):
        raise ApiError(400, "Field width/length must be 1-1000 m")
    mx, my = CROPS[main]["spacing"]
    px, py = CROPS[partner]["spacing"]
    nx, ny = int(W // mx), int(L // my)
    if nx < 1 or ny < 2:
        raise ApiError(400, "Field too small for %s spacing (%.1f x %.1f m)" % (main, mx, my))
    ox, oy = (W - nx * mx) / 2, (L - ny * my) / 2
    main_pts = [[round(ox + (i + .5) * mx, 2), round(oy + (j + .5) * my, 2)] for j in range(ny) for i in range(nx)]
    clear = min(1.0, my / 4)
    rows, count = [], 0
    for j in range(ny - 1):
        lo, hi = oy + (j + .5) * my + clear, oy + (j + 1.5) * my - clear
        y = lo + py / 2
        while y <= hi + 1e-9:
            n = int(W // px)
            if n:
                rows.append({"y": round(y, 2), "x0": round((W - n * px) / 2 + px / 2, 2), "step": px, "n": n})
                count += n
            y += py
    pc, mc = CROPS[partner]["plant_cost"], CROPS[main]["plant_cost"]
    return {"main": main, "partner": partner, "width": W, "length": L, "main_spacing": [mx, my], "partner_spacing": [px, py],
            "main_count": len(main_pts), "partner_count": count, "main_points": main_pts[:3000], "partner_rows": rows,
            "main_plant_cost": round(len(main_pts) * mc), "partner_plant_cost": round(count * pc),
            "note": "Illustrative layout from sample spacing rules, not a universal planting rule. " + NOTE}


def market(crop):
    c = _crop(crop)
    idx = [1.15 if m in c["peak"] else 0.88 if m in c["low"] else 1.0 for m in range(1, 13)]
    prices = [round(c["price"] * f) for f in idx]
    best = sorted(range(12), key=lambda i: -prices[i])[:3]
    return {"crop": crop, "unit": c["unit"], "base_price": c["price"], "monthly": prices,
            "best_months": sorted(i + 1 for i in best),
            "note": "Sample seasonal pattern, not live prices. Connect a trusted price source before relying on it."}


def _fractions(data):
    import numpy as np
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        img = img.convert("RGB").resize((96, 96))
    except Exception:
        raise ApiError(400, "Could not read the image. Upload a JPG or PNG leaf photo.")
    hsv = np.asarray(img.convert("HSV")).reshape(-1, 3).astype(int)
    h, s, v = hsv[:, 0], hsv[:, 1], hsv[:, 2]
    taken = np.zeros(len(h), bool)
    masks = {}
    for name, m in (("dark", v < 70), ("white", (s < 35) & (v > 190)), ("green", (h >= 45) & (h <= 110) & (s >= 50)),
                    ("yellow", (h >= 27) & (h < 45) & (s >= 70) & (v >= 120)),
                    ("orange", (h >= 8) & (h < 27) & (s >= 120) & (v >= 150)),
                    ("brown", (h >= 5) & (h < 30) & (s >= 60))):
        m = m & ~taken
        masks[name] = int(m.sum())
        taken |= m
    leaf = sum(masks.values())
    if leaf < 0.05 * len(h):
        raise ApiError(400, "No leaf area detected. Take a close, well-lit photo of the leaf.")
    return {k: n / leaf for k, n in masks.items()}


def detect(data, crop, symptoms=()):
    """Heuristic screening: leaf colour analysis + reported symptoms matched to a knowledge base.
    NOT a trained model (planned: transfer learning on PlantVillage). Advice needs expert validation."""
    _crop(crop)
    symptoms = {s for s in symptoms if s}
    fr = _fractions(data)
    affected = sum(fr[k] for k in ("yellow", "orange", "brown", "dark", "white"))
    sev = "mild" if affected < .15 else "moderate" if affected < .35 else "severe"
    res = {"crop": crop, "affected_pct": round(affected * 100, 1), "colors": {k: round(v * 100, 1) for k, v in fr.items()},
           "disclaimer": "Prototype screening using leaf colour and reported symptoms. It is not a trained diagnostic model; confirm with an agriculture officer."}
    if affected < .05 and not symptoms:
        return {**res, "status": "healthy", "severity": "none", "matches": [],
                "message": "Leaf looks mostly healthy. Keep scouting regularly."}
    matches = []
    for d in DISEASES:
        if crop not in d["crops"]:
            continue
        raw = 2 * len(symptoms & set(d["sym"])) + 6 * sum(fr[c] for c in d["col"])
        norm = min(1.0, raw / (2 * len(d["sym"]) + 3))
        matches.append({"id": d["id"], "name": d["name"], "match_pct": round(norm * 100), "treatment": d["treat"], "prevention": d["prevent"]})
    matches.sort(key=lambda m: -m["match_pct"])
    return {**res, "status": "possible_issue", "severity": sev if affected >= .05 else "unclear", "matches": matches[:3],
            "message": "Possible issues ranked by indicative match. Severity is estimated from visible affected leaf area."}
