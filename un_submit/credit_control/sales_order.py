import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    base_url = frappe.utils.get_url()

    sales_order_url = f"{base_url}/app/sales-order/{doc.name}"
    justification_url = f"{sales_order_url}#justification"
    cancel_order_url = f"{base_url}/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"

    html_message = f"""
<b>🛑 Sales Order Blocked Due to Overdue!</b><br><br>

<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
    <tr><th align="left">Field</th><th align="left">Value</th></tr><br>
    <tr><td><b>Sales Order</b></td><td><a href="{sales_order_url}">{doc.name}</a></td></tr><br>
    <tr><td><b>Customer</b></td><td>{doc.customer_name}</td></tr><br>
    <tr><td><b>Created By</b></td><td>{doc.owner}</td></tr><br>
    <tr><td><b>Date</b></td><td>{doc.creation.strftime('%Y-%m-%d')}</td></tr><br>
</table><br>

<b>👉 Next Actions:</b><br>
📝 <a href="{justification_url}">Submit Justification</a><br>
❌ <a href="{cancel_order_url}">Cancel Order</a>
"""

    # Raven Webhook
    raven_url = "http://62.171.191.18/api/method/raven.api.raven_message.send_message"

    headers = {
        "Authorization": "token e9ffc25922df3cd:7398f8d1116bf33",
        "Content-Type": "application/json"
    }

    payload = {
        "channel_id": "general",
        "text": html_message,
        "is_html": True  # This tells Raven to render the message as HTML
    }

    try:
        res = requests.post(raven_url, headers=headers, json=payload)
        res.raise_for_status()
        return "Notification sent to Raven."
    except requests.RequestException as e:
        frappe.log_error(str(e), "Raven Notification Failed")
        return "Failed to send notification"