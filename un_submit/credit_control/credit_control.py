@frappe.whitelist()
def validate_credit_block(doc, method):
    from frappe.utils import today, add_days
    import requests

    overdue = frappe.get_all("Sales Invoice", filters={
        "customer": doc.customer,
        "outstanding_amount": [">", 0],
        "due_date": ["<", add_days(today(), -15)],
        "docstatus": 1
    })

    justification_exists = frappe.db.exists("Sales Order Override Justification", {
        "sales_order": doc.name,
        "status": "Pending"
    })

    if overdue and not justification_exists:
        try:
            requests.post("https://n8n.mdpl.org.in/webhook/erpnext-credit-block", json={
                "sales_order": doc.name,
                "customer": doc.customer,
                "reason": "Overdue invoices > 15 days"
            })
        except Exception as e:
            frappe.log_error(str(e), "Webhook Failed")

        frappe.throw("Blocked: Customer has overdue invoices > 15 days. Please submit justification.")