import frappe
from frappe.utils import today, add_days

@frappe.whitelist()
def check_overdue_for_customer(customer, sales_order=None):
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    overdue_limit = frappe.db.get_value("Customer Group", customer_group, "custom_overdue_days_limit") or 15

    overdue_invoices = frappe.get_all("Sales Invoice", filters={
        "customer": customer,
        "docstatus": 1,
        "outstanding_amount": [">", 0],
        "due_date": ["<", add_days(today(), -int(overdue_limit))]
    })

    # Check if justification exists with "Approved" status
    justification_exists = False
    if sales_order:
        justification_exists = frappe.db.exists("Sales Order Override Justification", {
            "sales_order": sales_order,
            "status": "Approved"
        })

    return {
        "is_blocked": bool(overdue_invoices),
        "justification_approved": bool(justification_exists),
        "overdue_limit": overdue_limit
    }
