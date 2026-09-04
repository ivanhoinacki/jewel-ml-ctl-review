from fastapi import FastAPI
from fastapi.testclient import TestClient

from recs_api.placements import complete_the_look as ctl


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        self.docs = sorted(self.docs, key=lambda d: d.get(key, 0), reverse=direction == -1)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeCatalog:
    def __init__(self, docs):
        self.docs = docs

    def find_one(self, query):
        return next((d for d in self.docs if all(d.get(k) == v for k, v in query.items())), None)

    def find(self, query, projection=None):
        def match(d):
            for k, v in query.items():
                if isinstance(v, dict) and "$ne" in v:
                    if d.get(k) == v["$ne"]:
                        return False
                elif d.get(k) != v:
                    return False
            return True

        return FakeCursor([d for d in self.docs if match(d)])


def item(sku, **overrides):
    base = {
        "integration_id": "acme",
        "sku": sku,
        "category": "shoes",
        "title": f"Item {sku}",
        "url": f"https://acme.test/p/{sku}",
        "image": {"url": f"https://cdn.acme.test/{sku}.jpg"},
        "price": 10.0,
        "brand": "Acme",
        "popularity": 1,
    }
    base.update(overrides)
    return base


def make_client(docs, monkeypatch):
    monkeypatch.setattr(ctl, "catalog", FakeCatalog(docs))
    app = FastAPI()
    app.include_router(ctl.router)
    return TestClient(app)


def test_missing_anchor_returns_empty(monkeypatch):
    client = make_client([item("a")], monkeypatch)
    r = client.get("/v1/acme/complete-the-look?sku=nope")
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_anchor_without_category_returns_empty(monkeypatch):
    client = make_client([item("a", category=None)], monkeypatch)
    r = client.get("/v1/acme/complete-the-look?sku=a")
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_partial_item_is_dropped_not_fatal(monkeypatch):
    docs = [item("a"), item("b"), item("c", image={}), item("d", url=None)]
    client = make_client(docs, monkeypatch)
    r = client.get("/v1/acme/complete-the-look?sku=a")
    assert r.status_code == 200
    assert [i["sku"] for i in r.json()["items"]] == ["b"]


def test_anchor_excluded_from_results(monkeypatch):
    client = make_client([item("a"), item("b")], monkeypatch)
    skus = [i["sku"] for i in client.get("/v1/acme/complete-the-look?sku=a").json()["items"]]
    assert "a" not in skus


def test_limit_is_clamped(monkeypatch):
    docs = [item("a")] + [item(f"x{i}") for i in range(60)]
    client = make_client(docs, monkeypatch)
    assert client.get("/v1/acme/complete-the-look?sku=a&limit=100000").status_code == 422
    r = client.get(f"/v1/acme/complete-the-look?sku=a&limit={ctl.MAX_LIMIT}")
    assert len(r.json()["items"]) == ctl.MAX_LIMIT


def test_price_leaves_as_amount_and_currency(monkeypatch):
    docs = [item("a"), item("b", price=None, currency="MXN"), item("c", price="12.50")]
    client = make_client(docs, monkeypatch)
    by_sku = {i["sku"]: i for i in client.get("/v1/acme/complete-the-look?sku=a").json()["items"]}
    assert by_sku["b"]["price"] == {"amount": None, "currency": "MXN"}
    assert by_sku["c"]["price"] == {"amount": None, "currency": "USD"}
    assert "formatted" not in by_sku["b"]["price"]
