import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    base_url = frappe.utils.get_url()
    sales_order_url = f"{base_url}/app/sales-order/{doc.name}"
    justification_url = f"{sales_order_url}#justification"
    cancel_url = f"{base_url}/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"
    subject = "Sales Order Blocked Due to Overdue!"
    raven_message = (
    f"Sales Order: {doc.name}<br>"
    f"Customer: {doc.customer_name}<br>"
    f"Created By: {doc.owner}<br>"
    f"Date: {doc.creation.strftime('%Y-%m-%d')}<br><br>"
    f"👉 Next Actions:<br><br>"
    f"📝 Submit Justification: <a href='{justification_url}'>{justification_url}</a><br><br>"
    f"❌ Cancel Order: <a href='{cancel_url}'>{cancel_url}</a>"
    )

rendered_message = Markup(
    f"<h2><b>{subject}</b></h2><br>"
    f"{raven_message}"
)



    raven_url = "http://62.171.191.18/api/method/raven.api.raven_message.send_message"
    headers = {
        "Authorization": "token e9ffc25922df3cd:7398f8d1116bf33",
        "Content-Type": "application/json"
    }
    payload = {
        "channel_id": "general",
        "text": rendered_message
    }

    try:
        res = requests.post(raven_url, headers=headers, json=payload)
        res.raise_for_status()
        return "Notification sent to Raven."
    except requests.RequestException as e:
        frappe.log_error(str(e), "Raven Notification Failed")
        return "Failed to send notification"
