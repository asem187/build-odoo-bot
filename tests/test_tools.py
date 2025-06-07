from src.agent import create_odoo, update_odoo

class DummyModel:
    def __init__(self):
        self.created = None
        self.updated = None
    def check_access_rights(self, right, raise_exception=False):
        pass
    def create(self, data):
        self.created = data
        return 1
    def write(self, ids, data):
        self.updated = (ids, data)
    def read(self, ids):
        return [{"id": ids[0], **(self.created or self.updated[1])}]

class DummyOdoo:
    def __init__(self):
        self.env = {"res.partner": DummyModel()}

def test_create(monkeypatch):
    odoo = DummyOdoo()
    monkeypatch.setattr('src.agent.get_connection', lambda: odoo)
    res = create_odoo({"model": "res.partner", "data": {"name": "John"}})
    assert res["name"] == "John"


def test_update(monkeypatch):
    odoo = DummyOdoo()
    monkeypatch.setattr('src.agent.get_connection', lambda: odoo)
    res = update_odoo({"model": "res.partner", "id": 1, "data": {"name": "Jane"}})
    assert res["name"] == "Jane"
