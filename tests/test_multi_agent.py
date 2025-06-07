from src.agent import MultiAgent

class Dummy:
    def __init__(self, name):
        self.name = name
        self.last = None
    def run(self, message):
        self.last = message
        return self.name

def test_routing():
    crm = Dummy('crm')
    accounting = Dummy('accounting')
    ma = MultiAgent(crm_agent=crm, accounting_agent=accounting)
    assert ma.run('Show me an invoice') == 'accounting'
    assert accounting.last == 'Show me an invoice'
    assert ma.run('Find customer John') == 'crm'
    assert crm.last == 'Find customer John'


class DummyEmbedder:
    def embed_query(self, text):
        if 'invoice' in text or 'account' in text:
            return [1.0, 0.0]
        return [0.0, 1.0]


def test_embedding_routing():
    crm = Dummy('crm')
    accounting = Dummy('accounting')
    embedder = DummyEmbedder()
    ma = MultiAgent(
        crm_agent=crm,
        accounting_agent=accounting,
        classifier='embedding',
        embedder=embedder,
    )
    assert ma.run('Please create an invoice') == 'accounting'
    assert ma.run('Add a new lead') == 'crm'
