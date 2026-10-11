import base64, hashlib, hmac, json, os, secrets, time

SECRET = os.environ.get("AGRISHIELD_SECRET", "dev-secret-change-me").encode()


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt, hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()


def check_pw(pw, salt, h):
    return hmac.compare_digest(hash_pw(pw, salt)[1], h)


def _sig(p):
    return hmac.new(SECRET, p.encode(), "sha256").hexdigest()


def make_token(uid, role, ttl=7 * 86400):
    p = base64.urlsafe_b64encode(json.dumps({"uid": uid, "role": role, "exp": int(time.time()) + ttl}).encode()).decode()
    return p + "." + _sig(p)


def read_token(t):
    try:
        p, sig = t.split(".")
        if not hmac.compare_digest(sig, _sig(p)):
            return None
        d = json.loads(base64.urlsafe_b64decode(p.encode()))
        return d if d["exp"] > time.time() else None
    except Exception:
        return None
