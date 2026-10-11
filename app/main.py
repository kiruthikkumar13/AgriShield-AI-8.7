"""FastAPI app. Thin routes over app.services / app.engine. Run: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import engine, services as S
from .db import connect
from .errors import ApiError
from .knowledge import CROPS, DISTRICTS, INTERCROP, SEASONS, SOILS, SYMPTOMS, WATER
from .seed import seed

@contextmanager
def session():
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app):
    with session() as db:
        seed(db)
    yield


app = FastAPI(title="AgriShield AI", version="1.0", lifespan=lifespan)
STATIC = Path(__file__).resolve().parent.parent / "static"


@app.exception_handler(ApiError)
async def _api_error(request, exc):
    return JSONResponse({"detail": exc.msg}, status_code=exc.status)


async def body(request):
    try:
        d = await request.json()
    except Exception:
        raise ApiError(400, "Invalid JSON body")
    if not isinstance(d, dict):
        raise ApiError(400, "JSON object expected")
    return d


def me(request, db, required=True):
    h = request.headers.get("authorization", "")
    if not h.lower().startswith("bearer "):
        if required:
            raise ApiError(401, "Please log in")
        return None
    return S.user_from_token(db, h[7:].strip())


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/meta")
def meta():
    return {"crops": {k: {"ta": v["ta"], "unit": v["unit"], "price": v["price"]} for k, v in CROPS.items()},
            "districts": list(DISTRICTS), "soils": SOILS, "water": WATER, "seasons": SEASONS,
            "symptoms": SYMPTOMS, "intercrop": INTERCROP}


@app.post("/api/register")
async def register(request: Request):
    d = await body(request)
    with session() as db:
        return S.register(db, d)


@app.post("/api/login")
async def login(request: Request):
    d = await body(request)
    with session() as db:
        return S.login(db, d)


@app.get("/api/me")
async def whoami(request: Request):
    with session() as db:
        return S._pub(me(request, db))


@app.post("/api/recommend")
async def recommend(request: Request):
    d = await body(request)
    return engine.recommend(d.get("soil") or None, d.get("water") or None, d.get("season"), d.get("acres") or 1, d.get("district") or None)


@app.post("/api/economics")
async def economics(request: Request):
    d = await body(request)
    return engine.economics(d.get("crop"), d.get("acres") or 1, d.get("price"))


@app.post("/api/intercrop")
async def intercrop(request: Request):
    d = await body(request)
    return engine.intercrop_layout(d.get("main"), d.get("partner"), d.get("width"), d.get("length"))


@app.get("/api/market")
def market(crop: str):
    return engine.market(crop)


@app.post("/api/detect")
async def detect(request: Request):
    form = await request.form()
    f = form.get("image")
    if f is None or not hasattr(f, "read"):
        raise ApiError(400, "Attach a leaf image in the 'image' field")
    data = await f.read()
    if not data or len(data) > 5 * 1024 * 1024:
        raise ApiError(400, "Image must be between 1 byte and 5 MB")
    crop = str(form.get("crop") or "")
    result = engine.detect(data, crop, [s.strip() for s in str(form.get("symptoms") or "").split(",")])
    with session() as db:
        u = me(request, db, required=False)
        if u:
            S.save_scan(db, u, crop, result)
    return result


@app.get("/api/scans")
async def scans(request: Request):
    with session() as db:
        return S.list_scans(db, me(request, db))


@app.get("/api/listings")
async def listings(request: Request, crop: str = "", district: str = "", mine: int = 0):
    with session() as db:
        u = me(request, db, required=bool(mine))
        return S.list_listings(db, crop, district, u["id"] if mine else None)


@app.post("/api/listings")
async def new_listing(request: Request):
    d = await body(request)
    with session() as db:
        return S.create_listing(db, me(request, db), d)


@app.post("/api/orders")
async def new_order(request: Request):
    d = await body(request)
    with session() as db:
        return S.place_order(db, me(request, db), d)


@app.get("/api/orders")
async def orders(request: Request):
    with session() as db:
        return S.my_orders(db, me(request, db))


@app.post("/api/orders/{oid}/status")
async def order_status(oid: int, request: Request):
    d = await body(request)
    with session() as db:
        return S.update_order(db, me(request, db), oid, d.get("status"))


@app.post("/api/requests")
async def new_request(request: Request):
    d = await body(request)
    with session() as db:
        return S.create_request(db, me(request, db), d)


@app.get("/api/requests")
async def requests_(request: Request):
    with session() as db:
        return S.list_requests(db, me(request, db))


@app.get("/api/requests/{rid}/offers")
async def offers(rid: int, request: Request):
    with session() as db:
        return S.request_offers(db, me(request, db), rid)


@app.post("/api/offers")
async def new_offer(request: Request):
    d = await body(request)
    with session() as db:
        return S.make_offer(db, me(request, db), d)


@app.post("/api/offers/{oid}/accept")
async def accept(oid: int, request: Request):
    with session() as db:
        return S.accept_offer(db, me(request, db), oid)


@app.get("/api/services")
def services(district: str = ""):
    with session() as db:
        return S.list_services(db, district)


@app.post("/api/services")
async def new_service(request: Request):
    d = await body(request)
    with session() as db:
        return S.add_service(db, me(request, db), d)


@app.post("/api/service-requests")
async def new_service_request(request: Request):
    d = await body(request)
    with session() as db:
        return S.request_service(db, me(request, db), d)


@app.get("/api/service-requests")
async def service_requests(request: Request):
    with session() as db:
        return S.my_service_requests(db, me(request, db))


@app.post("/api/service-requests/{rid}/status")
async def service_request_status(rid: int, request: Request):
    d = await body(request)
    with session() as db:
        return S.update_service_request(db, me(request, db), rid, d.get("status"))


app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
