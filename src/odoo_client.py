"""Utility to obtain an Odoo RPC connection."""
import os
import odoorpc
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USERNAME = os.getenv("ODOO_USERNAME")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")


def get_connection():
    odoo = odoorpc.ODOO(ODOO_URL, protocol="jsonrpc")
    odoo.login(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    return odoo
