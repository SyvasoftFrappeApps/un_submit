import frappe
from frappe.utils import today, add_days

@frappe.whitelist()
def check_overdue_for_customer(customer, sales_order=None):
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    overdue_limit = frappe.db.get_value("Customer Group", customer_group, "custom_overdue_days_limit") or 15

    # Get overdue invoices
    overdue_invoices = frappe.get_all("Sales Invoice", filters={
        "customer": customer,
        "docstatus": 1,
        "outstanding_amount": [">", 0],
        "due_date": ["<", add_days(today(), -int(overdue_limit))]
    }, fields=["name", "outstanding_amount", "due_date"])

    # Calculate total overdue amount
    total_overdue_amount = sum(inv.outstanding_amount for inv in overdue_invoices)

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
        "overdue_limit": overdue_limit,
        "overdue_amount": total_overdue_amount
    }
