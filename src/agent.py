"""LangChain agents for interacting with Odoo and an orchestrator."""
import os
from typing import Dict, Optional, Any, List
import numpy as np

from dotenv import load_dotenv
from langchain.agents import Tool, AgentType, initialize_agent
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Support optional alternative API endpoints such as OpenRouter
def get_llm() -> ChatOpenAI:
    """Return a ChatOpenAI instance with optional custom base URL."""
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL")
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        if os.getenv("OPENROUTER_API_KEY")
        else os.getenv("OPENAI_API_KEY")
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    return ChatOpenAI(base_url=base_url, api_key=api_key, model=model)
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain

from .odoo_client import get_connection

load_dotenv()

INDEX_PATH = os.getenv("INDEX_PATH", "data/index")


def search_odoo(params: Dict[str, str]):
    """Search Odoo records by name."""
    model = params.get("model")
    query = params.get("query")
    odoo = get_connection()
    env_model = odoo.env[model]
    ids = env_model.search([("name", "ilike", query)])
    return env_model.read(ids)


def create_odoo(params: Dict[str, Any]):
    """Create a new Odoo record."""
    model = params.get("model")
    data = params.get("data", {})
    odoo = get_connection()
    env_model = odoo.env[model]
    env_model.check_access_rights("create", raise_exception=True)
    new_id = env_model.create(data)
    return env_model.read([new_id])[0]


def update_odoo(params: Dict[str, Any]):
    """Update an existing Odoo record."""
    model = params.get("model")
    record_id = params.get("id")
    data = params.get("data", {})
    odoo = get_connection()
    env_model = odoo.env[model]
    env_model.check_access_rights("write", raise_exception=True)
    env_model.write([record_id], data)
    return env_model.read([record_id])[0]


# Specialized search helpers used by individual agents

def search_crm(query: str):
    return search_odoo({"model": "res.partner", "query": query})


def search_accounting(query: str):
    return search_odoo({"model": "account.move", "query": query})


# Agent factories

def _build_agent(tools: List[Tool]) -> ConversationalRetrievalChain:
    llm = get_llm()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, memory=memory, verbose=True)
    if os.path.exists(INDEX_PATH):
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(INDEX_PATH, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        return ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory, combine_docs_chain=agent.chain)
    return agent


def get_crm_agent() -> ConversationalRetrievalChain:
    tools = [
        Tool(
            name="search_crm",
            func=search_crm,
            description="Search CRM contacts by name",
        ),
        Tool(
            name="create_record",
            func=create_odoo,
            description="Create an Odoo record given model and data",
        ),
        Tool(
            name="update_record",
            func=update_odoo,
            description="Update an Odoo record by id with new data",
        ),
    ]
    return _build_agent(tools)


def get_accounting_agent() -> ConversationalRetrievalChain:
    tools = [
        Tool(
            name="search_accounting",
            func=search_accounting,
            description="Search accounting records by name",
        ),
        Tool(
            name="create_record",
            func=create_odoo,
            description="Create an Odoo record given model and data",
        ),
        Tool(
            name="update_record",
            func=update_odoo,
            description="Update an Odoo record by id with new data",
        ),
    ]
    return _build_agent(tools)


class MultiAgent:
    """Simple router that dispatches to specialized agents."""

    def __init__(
        self,
        crm_agent: Optional[ConversationalRetrievalChain] = None,
        accounting_agent: Optional[ConversationalRetrievalChain] = None,
        classifier: str = "keywords",
        embedder: Optional[OpenAIEmbeddings] = None,
    ):
        self.crm_agent = crm_agent or get_crm_agent()
        self.accounting_agent = accounting_agent or get_accounting_agent()
        self.classifier = os.getenv("CLASSIFIER_MODE", classifier)
        if self.classifier == "embedding":
            self.embedder = embedder or OpenAIEmbeddings()
            self.acc_vec = self.embedder.embed_query(
                "invoice bill payment account expense journal"
            )
            self.crm_vec = self.embedder.embed_query(
                "lead customer opportunity crm contact"
            )

    def _cosine(self, a: List[float], b: List[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def classify(self, message: str) -> str:
        if getattr(self, "classifier", "keywords") == "embedding":
            vec = self.embedder.embed_query(message)
            acc_score = self._cosine(vec, self.acc_vec)
            crm_score = self._cosine(vec, self.crm_vec)
            return "accounting" if acc_score > crm_score else "crm"

        msg = message.lower()
        accounting_keywords = {"invoice", "bill", "payment", "account", "expense", "journal"}
        crm_keywords = {"lead", "customer", "opportunity", "crm", "contact"}
        acc_score = sum(k in msg for k in accounting_keywords)
        crm_score = sum(k in msg for k in crm_keywords)
        return "accounting" if acc_score > crm_score else "crm"

    def run(self, message: str):
        if self.classify(message) == "accounting":
            return self.accounting_agent.run(message)
        return self.crm_agent.run(message)


def get_agent() -> MultiAgent:
    """Return the multi-agent orchestrator."""
    classifier = os.getenv("CLASSIFIER_MODE", "keywords")
    return MultiAgent(classifier=classifier)
