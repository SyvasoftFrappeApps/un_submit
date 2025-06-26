import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    base_url = frappe.utils.get_url()

    sales_order_url = f"{base_url}/app/sales-order/{doc.name}"
    justification_url = f"{sales_order_url}#justification"
    cancel_url = f"{base_url}/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"

    message = f"""
```text
🛑 Sales Order Blocked Due to Overdue!

Sales Order     : {doc.name}
Customer        : {doc.customer_name}
Created By      : {doc.owner}
Date            : {doc.creation.strftime('%Y-%m-%d')}


👉 Next Actions:
📝 Submit Justification → {justification_url}
❌ Cancel Order         → {cancel_url}
"""

    # Raven Webhook
    raven_url = "http://62.171.191.18/api/method/raven.api.raven_message.send_message"

    headers = {
        "Authorization": "token e9ffc25922df3cd:7398f8d1116bf33",
        "Content-Type": "application/json"
    }

    payload = {
        "channel_id": "general",
        "text": message
    }

    try:
        res = requests.post(raven_url, headers=headers, json=payload)
        res.raise_for_status()
        return "Notification sent to Raven."
    except requests.RequestException as e:
        frappe.log_error(str(e), "Raven Notification Failed")
        return "Failed to send notification"
