import frappe
from frappe import _

def before_cancel(doc, method):
    if doc.get("ignore_linked_document"):
        doc.flags.ignore_links = True
