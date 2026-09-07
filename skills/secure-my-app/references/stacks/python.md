# Python: Django, FastAPI, SQLAlchemy

The per-stack answer to the FIX column in `controls.md`. Control IDs are the anchors.

Two opposite audits live in this file.

**Django ships secure and people switch things off.** Your job is subtraction: find the `csrf_exempt`,
the `DEBUG = True`, the `ALLOWED_HOSTS = ['*']`, the `mark_safe`. Django also gives you a single
command that grades its own deployment, and almost nothing in the security-tooling world bothers to
run it.

**FastAPI ships with nothing on and people add things halfway.** Your job is addition, and the
characteristic failure is a dependency that returns `None` instead of raising, in a handler that then
carries on as if a user were present.

---

## How to fingerprint this stack

| Marker | What it proves |
| --- | --- |
| `manage.py` at repo root | Django |
| `settings.py`, or `settings/` with `base.py` and `production.py` | Django settings. Read the production one, not `base` |
| `Django` in `requirements.txt` / `pyproject.toml` / `Pipfile` | Confirms the version. Pin it before writing a fix |
| `urls.py` with `urlpatterns` | Django routes |
| `rest_framework` in `INSTALLED_APPS` | Django REST Framework. Permissions live in serializers and viewsets, not only in views |
| `fastapi` in dependencies | FastAPI |
| `@app.get(` / `@router.post(` | FastAPI or a Starlette router |
| `from fastapi import Depends` | Dependency-based auth. Read every one of them |
| `sqlalchemy` in dependencies | SQLAlchemy. Check `1.4` versus `2.0`; the execute API differs |
| `alembic/` | SQLAlchemy migrations |
| `models.py` with `models.Model` | Django ORM |
| `pydantic` v1 versus v2 | `.dict()` versus `.model_dump()`, and different validator syntax |

```bash
python -c "import django; print(django.get_version())" 2>/dev/null
rg -n '^(Django|fastapi|sqlalchemy|pydantic)' requirements*.txt pyproject.toml 2>/dev/null
rg -n 'DEBUG|ALLOWED_HOSTS|SECRET_KEY' --glob '*settings*.py'
```

---

## The exact commands

### Django's own deployment grader

```bash
python manage.py check --deploy
```

Run it with the production settings module, or it grades the wrong file:

```bash
DJANGO_SETTINGS_MODULE=<your_project>.settings.production python manage.py check --deploy
# or
python manage.py check --deploy --settings=<your_project>.settings.production
```

It emits `security.W0xx` warnings, one per missing setting, and exits non-zero when there are issues.
Paste its real output into the PROOF field and tag it `[executed]`. This is the strongest tier 2
evidence available in this stack without touching the network, and it maps almost one-to-one onto the
P9, P10 and D2 controls.

For CI, `--fail-level WARNING` turns any warning into a non-zero exit.

### Reach the database

```bash
python manage.py dbshell -c "\dt"                       # Django, Postgres
psql "$DATABASE_URL" -c "\d+ <your_table>"              # direct
python manage.py showmigrations                          # what has actually run
```

Postgres RLS is usually `N/A` on both Django and FastAPI: the app connects as one role and filters in
the ORM. Say so and put the weight on R4, R5 and R6 rather than reporting every table as R1.

### Enumerate FastAPI routes and their dependencies

```bash
rg -n '@(app|router)\.(get|post|put|patch|delete)\(' --glob '!.venv' -A3
rg -n 'Depends\(' --glob '!.venv'
rg -n 'auto_error\s*=\s*False' --glob '!.venv'
```

Every route whose decorator has no `dependencies=` and whose signature has no `Depends` on an auth
callable is a D1 candidate. Every `auto_error=False` is a D9 candidate.

FastAPI serves its own route inventory at `$URL/openapi.json`. If that returns the full schema on a
production host, that is an information-disclosure finding; `FastAPI(openapi_url=None)` disables it.

---

## Fixes by control ID

## Django

### V3, P10, D2, P9. The settings block

Every one of these is checked by `manage.py check --deploy`. Fix them together, then re-run the
command and paste the clean output as the VERIFY.

```python
# <your_project>/settings/production.py
import os

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']      # KeyError at boot beats a silent default
ALLOWED_HOSTS = ['app.example.com', 'www.example.com']   # never ['*']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS. Start small, verify, then raise. Read the warning below before setting this.
SECURE_HSTS_SECONDS = 300                  # then 3600, then 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False     # only once every subdomain is HTTPS
SECURE_HSTS_PRELOAD = False                # not on day one

# headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
```

`django.middleware.security.SecurityMiddleware` must be in `MIDDLEWARE`, near the top, or none of the
`SECURE_*` settings do anything. `django.middleware.csrf.CsrfViewMiddleware` and
`django.middleware.clickjacking.XFrameOptionsMiddleware` must be there too.

Django's own HSTS warning, verbatim, and the reason for the ramp:

> The HSTS policy applies to your entire domain, not just the URL of the response that you set the
> header on. Therefore, you should only use it if your entire domain is served via HTTPS only.
>
> Browsers properly respecting the HSTS header will refuse to allow users to bypass warnings and
> connect to a site with an expired, self-signed, or otherwise invalid SSL certificate. If you use
> HSTS, make sure your certificates are in good shape and stay that way!

`SECURE_REFERRER_POLICY` accepts `no-referrer`, `no-referrer-when-downgrade`, `origin`,
`origin-when-cross-origin`, `same-origin`, `strict-origin`, `strict-origin-when-cross-origin`,
`unsafe-url`. `SECURE_CROSS_ORIGIN_OPENER_POLICY` accepts `same-origin` (the default and most secure),
`same-origin-allow-popups`, `unsafe-none`.

Behind a TLS-terminating proxy you also need `SECURE_PROXY_SSL_HEADER`, and Django is blunt about it:
"Failure to do this can result in CSRF vulnerabilities, and failure to do it correctly can also be
dangerous!" Set it only once you have confirmed the proxy strips that header from inbound requests, or
a client can claim HTTPS by sending it.

### P4. CSRF

Django's CSRF middleware protects every cookie-authenticated POST by default. The finding is where
someone turned it off.

```bash
rg -n '@csrf_exempt|csrf_exempt\(|CsrfViewMiddleware' --glob '!.venv'
```

Django: "Be very careful with marking views with the `csrf_exempt` decorator unless it is absolutely
necessary." Each hit needs a reason. The legitimate one is a webhook receiver authenticated by a
provider signature (see P8). The illegitimate one, and it is the common one, is "the AJAX call was
failing", which means the front end was not sending the token.

```python
# fix: send the token instead of exempting the view
CSRF_TRUSTED_ORIGINS = ['https://app.example.com']
```

Removing `django.middleware.csrf.CsrfViewMiddleware` from `MIDDLEWARE` disables CSRF site-wide with no
warning anywhere but `check --deploy`. Check for its presence, not just for the decorator.

### P1. SQL injection

Django's ORM parameterizes. The escape hatches do not.

```bash
rg -n '\.raw\(|\.extra\(|RawSQL\(|cursor\.execute\(' --glob '!.venv'
```

Django: raw queries and custom SQL "should be used sparingly and you should always be careful to
properly escape any parameters that the user can control. In addition, you should exercise caution
when using `extra()` and `RawSQL`."

```python
# finding
User.objects.raw(f"SELECT * FROM auth_user WHERE email = '{request.GET['email']}'")

# fix: params, not formatting
User.objects.raw("SELECT * FROM auth_user WHERE email = %s", [request.GET['email']])

# same rule with a cursor
with connection.cursor() as cur:
    cur.execute("SELECT id FROM orders WHERE user_id = %s AND id = %s", [request.user.id, order_id])
```

`%s` here is a database placeholder, not Python string formatting. `cur.execute("... %s" % value)` is
injectable and looks almost identical. Grep for `%` and `.format(` and f-strings *inside* the SQL
string, not for `execute`.

### P3. XSS

Django templates autoescape. The finding is where that is undone.

```bash
rg -n 'mark_safe\(|\|safe\b|\{%\s*autoescape\s+off|format_html\(|is_safe\s*=\s*True' --glob '!.venv'
```

Django: "It is also important to be particularly careful when using the `is_safe` attribute with
custom template tags, the `safe` template tag, `mark_safe`, and when autoescape is turned off."

For each hit, trace whether the value can carry user input. A `mark_safe` over a literal is fine. A
`mark_safe` over a model field is the finding.

```python
# finding
mark_safe(f"<b>{user.display_name}</b>")

# fix: format_html escapes its arguments
from django.utils.html import format_html
format_html("<b>{}</b>", user.display_name)
```

And Django on stored HTML: "Unless the HTML is guaranteed to come from a trusted source - user input
is *not* a trusted source - stored HTML should be checked and sanitized, preferably on input as well
as output."

### P9 (Host header) and ALLOWED_HOSTS

`ALLOWED_HOSTS = ['*']` disables Host header validation, which enables cache poisoning and password
reset links pointing at an attacker's domain. Django validates the `Host` header against
`ALLOWED_HOSTS` in `HttpRequest.get_host()`, and adds: "This validation only applies via
`get_host()`; if your code accesses the `Host` header directly from `request.META` you are bypassing
this security protection."

```bash
rg -n "META\[['\"]HTTP_HOST" --glob '!.venv'
```

### R4 and R5. Ownership and tenancy

The filter belongs in the queryset, not in an `if` afterwards.

```python
# finding: object fetched by id alone
order = get_object_or_404(Order, pk=pk)

# fix: id AND the session subject
order = get_object_or_404(Order, pk=pk, user=request.user)

# multi-tenant: tenant from the session, never the request
qs = Invoice.objects.filter(org__memberships__user=request.user)
```

A class-based view's `get_queryset` is the right place, because every method on the view inherits it:

```python
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
```

With DRF, `permission_classes` on the viewset is the R10 control. Check `DEFAULT_PERMISSION_CLASSES`
in `REST_FRAMEWORK`; if it is unset, DRF's default is permissive and every view without an explicit
`permission_classes` is open.

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

### R6. Mass assignment

```python
# finding: every model field is writable, including is_staff and balance
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

# fix: name the fields, and mark the ones the server owns
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name']
        read_only_fields = ['id', 'email']
```

`fields = '__all__'` on a model with a `role`, `is_staff`, `plan`, `credits` or `balance` column is the
finding. Same for a Django `ModelForm` with no `fields` list.

```bash
rg -n "fields\s*=\s*'__all__'|exclude\s*=" --glob '!.venv'
```

`exclude` is a denylist and drifts: a column added next month is writable by default. Use `fields`.

---

## FastAPI

### D1. The auth check as a dependency

Two shapes, both documented. Use the decorator form when the handler does not need the user object,
and the parameter form when it does.

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/items/")
async def read_items(current_user: Annotated[User, Depends(get_current_user)]):
    return {"owner": current_user.username}
```

Decorator form, from FastAPI's own example:

```python
@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

The dependency denies by raising:

```python
async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
```

Router-level dependencies apply to every route on the router
(`APIRouter(dependencies=[Depends(get_current_user)])`); confirm the exact shape against
<https://fastapi.tiangolo.com/tutorial/bigger-applications/> before applying it, since the router
signature has moved between versions.

### D9. The fail-open dependency

This is the characteristic FastAPI bug and it has three forms.

**Form one, `auto_error=False`.** FastAPI: "By default, if the [credential] is not provided,
[the security class] will automatically cancel the request and send the client an error." But "If
`auto_error` is set to `False`, when the [credential] is not available, instead of erroring out, the
dependency result will be `None`."

```python
# finding: the scheme no longer rejects, and nothing else does either
security = HTTPBearer(auto_error=False)

@app.get("/admin")
async def admin(creds = Depends(security)):
    return {"secrets": load_everything()}      # creds is None, the handler runs anyway
```

`auto_error=False` is legitimate for genuinely optional auth. It is a finding whenever the handler
does not itself check for `None` and raise.

**Form two, the swallowed exception.**

```python
# finding
async def get_current_user(token = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return get_user(payload["sub"])
    except Exception:
        return None                # a bad token now means "anonymous", and the route still runs
```

The fix is to raise, never to return `None`, unless every caller checks.

**Form three, the inverted check.** `if user:` where `if not user:` was meant. It reads fine, tests
pass while you are logged in, and unauthenticated callers get through. Grep is weak here; read every
auth dependency body end to end.

VERIFY for all three: force the dependency to fail (no token, a garbage token, a wrong `SECRET_KEY`)
and confirm a `401`, never a `200` with data.

### D3. Password hashing

The current FastAPI docs use `pwdlib` (`pip install "pwdlib[argon2]"`), not `passlib`.

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)
```

`passlib` with `CryptContext(schemes=["bcrypt"])` is what older tutorials and older generated code
show. It still works and is no longer what the docs recommend. Treat existing `passlib` code as legacy
rather than a finding on its own; treat a raw `hashlib.sha256(password)` as a D3 finding.

### D4. JWT verification

```python
# fix, from the FastAPI docs
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

The library is PyJWT (`import jwt`, package `pyjwt`). Two failure modes:

- `options={"verify_signature": False}` accepts any token.
- `jwt.decode(...)` with no `algorithms` argument. Modern PyJWT requires it; confirm the installed
  version rather than assuming, since an old pin plus a missing `algorithms` is the `alg: none` hole.

Do not confuse PyJWT with `python-jose`. The import is `jwt` in both cases and the APIs differ. Read
the requirements file.

### P2 and V2. Validation is not authorization

Pydantic gives you P2 for free on every typed handler: a malformed body returns `422`, not `500`. It
gives you nothing for R4 or R6. A well-formed `order_id` can still name someone else's row, so the
ownership filter is still your job.

The half people skip is the response model:

```python
class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    # hashed_password, stripe_customer_id, is_superuser are absent on purpose

@app.get("/users/me", response_model=UserOut)
async def me(user = Depends(get_current_user)):
    return user      # extra attributes on `user` are filtered out by response_model
```

`response_model` is the V2 fix for this stack. Returning an ORM object with no `response_model` ships
every column the object has.

### V3. Errors

```python
app = FastAPI(debug=False)     # never True in production
```

Add a handler so an unexpected exception cannot return a traceback:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception("unhandled")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
```

---

## SQLAlchemy

### P1. `text()` with bound parameters

The correct form, from the SQLAlchemy 2.0 tutorial:

```python
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table WHERE y > :y"), {"y": 2})
    for row in result:
        print(f"x: {row.x}  y: {row.y}")
```

Named parameters use `:name` in the string and a dict in the second argument to `execute()`.

SQLAlchemy's own warning, verbatim:

> a Python literal value, even non-strings like integers or dates, should **never be stringified into
> SQL string directly**; a parameter should **always** be used. This is most famously known as how to
> avoid SQL injection attacks when the data is untrusted.

The findings:

```python
# f-string into text(): injectable
conn.execute(text(f"SELECT * FROM users WHERE email = '{email}'"))

# .format() into text(): injectable
conn.execute(text("SELECT * FROM users WHERE id = {}".format(user_id)))

# % into text(): injectable
conn.execute(text("SELECT * FROM users WHERE id = %s" % user_id))
```

```bash
rg -n 'text\(\s*f["\x27]|text\([^)]*\.format\(|text\([^)]*%\s' --glob '!.venv'
rg -n 'execute\(\s*f["\x27]|session\.execute\(\s*f["\x27]' --glob '!.venv'
```

A bound parameter binds a *value*. It cannot bind a table name, a column name, or `ASC`/`DESC`. If
user input picks a sort column, the fix is a dictionary allowlist:

```python
SORTABLE = {"created": Order.created_at, "total": Order.total}
column = SORTABLE.get(request_sort)
if column is None:
    raise HTTPException(status_code=400, detail="bad sort")
stmt = select(Order).order_by(column.desc())
```

### R4 with the ORM

```python
# finding
order = session.get(Order, order_id)

# fix
stmt = select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
order = session.scalars(stmt).one_or_none()
if order is None:
    raise HTTPException(status_code=404)
```

`session.get()` fetches by primary key with no other predicate. Every `session.get()` on a
user-owned table is an R4 candidate.

---

## Both frameworks

### P8. Webhook signatures, and constant-time comparison

Two things break a correct-looking webhook check in Python, and they are the same two that break it in
Node.

**The raw bytes must survive.** The signature was computed over the exact body the provider sent. Any
framework that parses JSON for you has already thrown those bytes away, so a re-serialized dict will
not match no matter how correct your HMAC is.

**The comparison must be constant time.** `==` on a digest leaks the answer through how long it takes
to fail. The stdlib answer is `hmac.compare_digest`, and Python's own docs say so: "When comparing the
output of `hexdigest()` to an externally supplied digest during a verification routine, it is
recommended to use the `compare_digest()` function instead of the `==` operator to reduce the
vulnerability to timing attacks."

```python
import hmac
import hashlib

def verify_signature(raw_body: bytes, received_sig: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),        # key must be bytes
        raw_body,               # the raw bytes, never a re-serialized dict
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received_sig)
```

The gotcha that bites, straight from the stdlib docs: the two arguments "must both be of the same
type: either `str` (ASCII only, as e.g. returned by `HMAC.hexdigest()`), or a bytes-like object."
Mixing a `str` and a `bytes` raises `TypeError`, and a `TypeError` inside a `try/except` that returns
`False`-ish is how this turns into a fail-open. Normalize both sides before comparing.

Django:

```python
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest

@csrf_exempt          # legitimate here: the signature IS the authentication
@require_POST
def stripe_webhook(request):
    sig = request.headers.get('Stripe-Signature', '')
    if not verify_signature(request.body, sig, settings.STRIPE_WEBHOOK_SECRET):
        return HttpResponseBadRequest('bad signature')
    return HttpResponse(status=200)
```

`request.body` is the raw request bytes. Read it before anything touches `request.POST`, because
Django can only hand out the raw stream once; confirm the exact exception and ordering against
<https://docs.djangoproject.com/en/stable/ref/request-response/> before relying on it.

This is also the one `@csrf_exempt` that P4 accepts. A webhook has no session cookie to forge, and the
provider signature is the authentication. Every other `csrf_exempt` still needs its own justification.

FastAPI:

```python
from fastapi import Request, HTTPException

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    raw = await request.body()          # bytes, before any Pydantic model touches it
    sig = request.headers.get("stripe-signature", "")
    if not verify_signature(raw, sig, STRIPE_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="bad signature")
    return {"ok": True}
```

Do not declare a Pydantic body model on a webhook route. Binding one makes FastAPI parse the body, and
the parsed object is not what the signature covers. Take the `Request` and read `await
request.body()` yourself. Confirm the `Request.body()` signature against
<https://fastapi.tiangolo.com/advanced/using-request-directly/> if the installed version is old.

Prefer the provider's own SDK verifier where one exists (`stripe.Webhook.construct_event` for Stripe
in Python), because it also enforces the timestamp tolerance that stops replay. Verify the exact
method name against <https://docs.stripe.com/webhooks> before applying it; hand it the raw bytes
either way.

**Use `hmac.compare_digest` for every attacker-supplied value you compare against a secret**, not just
webhooks: password reset tokens (D7), email verification tokens, API keys, and any session or
invitation identifier you look up by value. `token == stored_token` is the finding.

```bash
rg -n '(token|signature|secret|api_key|digest|hmac)\w*\s*==|==\s*\w*(token|signature|secret|digest)' \
  --glob '!.venv'
```

VERIFY: an unsigned POST to the webhook route returns 400, and a correctly signed one still returns
200. Both halves, per the paired test.

---

## The traps specific to this stack

| Trap | Why it looks right | What it actually does |
| --- | --- | --- |
| `DEBUG = True` in the deployed settings module | The repo's `settings.py` has `False` | Full traceback with locals and settings on every 500, SQL log, `ALLOWED_HOSTS` skipped. Check the module the deploy selects, not the safe default |
| `ALLOWED_HOSTS = ['*']` | It is the standard fix when a deploy returns 400 | Host header validation off permanently. Poisoned reset links, poisoned caches |
| `@csrf_exempt` left after debugging | The AJAX call was failing and this made it work | Every cookie-authenticated write on that view is forgeable. Each one needs a written reason |
| `CsrfViewMiddleware` removed from `MIDDLEWARE` | Same cause, no decorator to grep for | CSRF off site-wide. Only `check --deploy` tells you |
| `fields = '__all__'` | Concise, idiomatic DRF | Every column writable, `is_staff` and `balance` included. Mass assignment in one line |
| `mark_safe` over a model field | Django escapes by default so it feels safe to opt out | Stored XSS. Almost every Django XSS traces to `mark_safe`, `\|safe`, or `{% autoescape off %}` |
| No `response_model` on a FastAPI route returning an ORM object | Types look right in the editor | `hashed_password`, `stripe_customer_id`, `is_superuser` go out with it |
| `session.get(Model, id)` | Every ORM tutorial teaches it | Primary key and no other predicate. The most compact IDOR in the language |
| `text(f"...")` | Two characters from the safe form, right beside it in the docs | SQL injection |
| `if received_token == stored_token` | It is the obvious way to compare two strings | Leaks the secret one character at a time through response timing. Use `hmac.compare_digest` |
| A Pydantic model or `request.POST` on a webhook route | Typed, idiomatic, validated | The body is parsed before you see it, so the signature can never match the bytes you have |

Four that need more than a row.

**Nobody runs `manage.py check --deploy`.** It is the zero-install gate that grades the exact settings
this category argues about, and it produces real `[executed]` output. Run it with the production
settings module. Running it against `settings.py` when the project deploys `settings/production.py`
grades a file that never ships.

**FastAPI's `auto_error=False`.** It reads as a small ergonomic choice and it converts a security
scheme from an enforcer into an optional parameter. The scheme stops raising, the dependency yields
`None`, and the handler runs. If the handler does not check for `None` and raise, the endpoint is
public.

**A dependency that returns `None` on error.** Same class, other direction. A `try/except` around
`jwt.decode` that returns `None` turns an expired token, a rotated secret or a network blip into an
anonymous session the route treats as valid. Auth dependencies must raise. This is OWASP A10:2025,
mishandling of exceptional conditions, and it is the class behind the best-known AI-app breach.

**Pydantic validation mistaken for authorization.** A `422` on a malformed body says nothing about
whether the caller may touch the row a well-formed body names. An audit that stops at "it has Pydantic
models" has checked P2 and skipped the entire ROOMS group.

---

## Verified against

Checked 2026-09-06.

- <https://docs.djangoproject.com/en/stable/howto/deployment/checklist/> `manage.py check --deploy`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`
- <https://docs.djangoproject.com/en/5.2/ref/middleware/> `SecurityMiddleware` and every `SECURE_*` setting it reads, the `SECURE_REFERRER_POLICY` and `SECURE_CROSS_ORIGIN_OPENER_POLICY` value lists, the HSTS warning quoted verbatim
- <https://docs.djangoproject.com/en/stable/topics/security/> `csrf_exempt`, `raw()`/`extra()`/`RawSQL`, `mark_safe`/`safe`/`is_safe`/autoescape, `XFrameOptionsMiddleware`, `ALLOWED_HOSTS` and `get_host()`, the `SECURE_PROXY_SSL_HEADER` warning
- <https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html> `text()` with `:y` bind parameters and the "never be stringified into SQL string directly" warning
- <https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/> `dependencies=[Depends(...)]`, denying by raising `HTTPException`
- <https://fastapi.tiangolo.com/reference/security/> the security class names, `auto_error` default `True`, and the documented `None` behaviour when `auto_error=False`
- <https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/> `pwdlib` `PasswordHash.recommended()`, PyJWT `jwt.encode` / `jwt.decode(..., algorithms=[ALGORITHM])`, `InvalidTokenError`
- <https://docs.python.org/3/library/hmac.html> `hmac.new(key, msg, digestmod)`, `hmac.compare_digest(a, b)`, the same-type (`str` ASCII or bytes-like) requirement, and the timing-attack wording quoted above

Could not verify and must not be stated as fact:

- The specific `security.Wxxx` codes `check --deploy` emits per setting. Run the command and read the
  real codes out of its output rather than quoting one from memory.
- `--fail-level WARNING` on `manage.py check`. Confirm against
  <https://docs.djangoproject.com/en/stable/ref/django-admin/#check> before putting it in a CI fix.
- The exact `APIRouter(dependencies=[...])` signature. Confirm against
  <https://fastapi.tiangolo.com/tutorial/bigger-applications/>.
- DRF's default `DEFAULT_PERMISSION_CLASSES` value on the installed version. Confirm against
  <https://www.django-rest-framework.org/api-guide/permissions/> before writing a finding that depends
  on the default being permissive.
- Whether the installed PyJWT major requires `algorithms`. Read the pinned version.
- `django.utils.crypto.constant_time_compare`. It does not appear on Django's public utils reference,
  so this file does not use it. Use the stdlib `hmac.compare_digest`, which is documented.
- The exact behaviour when `request.body` is read after `request.POST` in Django. Confirm against
  <https://docs.djangoproject.com/en/stable/ref/request-response/>.
- Starlette's `await request.body()` signature on old FastAPI pins. Confirm against
  <https://fastapi.tiangolo.com/advanced/using-request-directly/>.
- `stripe.Webhook.construct_event` (the Python SDK spelling). Confirm against
  <https://docs.stripe.com/webhooks> before writing it into a fix.
