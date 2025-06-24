import frappe
from frappe.utils import today, add_days

@frappe.whitelist()
def validate_credit_block(doc, method):
    # Fetch Customer Group and custom overdue limit
    customer_group = frappe.db.get_value("Customer", doc.customer, "customer_group")
    overdue_limit = frappe.db.get_value("Customer Group", customer_group, "custom_overdue_days_limit") or 15

    # Get invoices overdue by that limit
    overdue = frappe.get_all("Sales Invoice", filters={
        "customer": doc.customer,
        "outstanding_amount": [">", 0],
        "due_date": ["<", add_days(today(), -int(overdue_limit))],
        "docstatus": 1
    })

    # Check for approved override justification
    justification_exists = frappe.db.exists("Sales Order Override Justification", {
        "sales_order": doc.name,
        "status": "Approved"
    })

    if overdue and not justification_exists:
        frappe.throw(
            f"Blocked: Customer has invoices overdue by more than {overdue_limit} days. Please submit and approve justification."
        )
