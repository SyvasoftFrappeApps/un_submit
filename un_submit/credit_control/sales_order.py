import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    base_url = frappe.utils.get_url()

    sales_order_url = f"{base_url}/app/sales-order/{doc.name}"
    justification_url = f"{sales_order_url}#justification"
    cancel_order_url = f"{base_url}/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"
    from un_submit.credit_control.credit_control import check_overdue_for_customer
    overdue_info = check_overdue_for_customer(doc.customer, doc.name)
    overdue_amount = overdue_info.get("overdue_amount", 0)
    overdue_days = overdue_info.get("overdue_limit", 0)
    html_message = f"""
<b>🛑 Sales Order Blocked Due to Overdue!</b><br><br>

<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
    <tr><td><b>Sales Order</b></td><td><a href="{sales_order_url}">{doc.name}</a></td></tr><br>
</table>
<table>
    <tr><td><b>Customer Name  : </b></td><td>{doc.customer_name}</td></tr><br>
</table>
<table>
    <tr><td><b>Order Date     : </b></td><td>{doc.creation.strftime('%Y-%m-%d')}</td></tr><br>
</table>
<table>
    <tr><td><b>Order Total    : </b></td><td>{doc.rounded_total}</td></tr><br>
</table>
<table>
    <tr><td><b>OverDue Amount : </b></td><td>{doc.rounded_total}</td></tr><br>
</table>

<b>👉 Next Actions:</b><br>
📝 <a href="{justification_url}">Submit Justification</a><br>
❌ <a href="{cancel_order_url}">Cancel Order</a>
"""

    # Raven Webhook
    raven_url = f"{base_url}/api/method/raven.api.raven_message.send_message"

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