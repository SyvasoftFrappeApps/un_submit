import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    
    # Customize your message
    message = f"""
🛑 *Sales Order Blocked Due to Overdue!*
• *Sales Order:* {doc.name}
• *Customer:* {doc.customer_name}
• *Created By:* {doc.owner}
• *Date:* {doc.creation.strftime('%Y-%m-%d')}
• *Overdue Amount:* ₹XX,XXX
• *Overdue Days:* XX

👉 Please provide justification to proceed or cancel the order.
"""

    # Raven API endpoint
    raven_url = "http://62.171.191.18/api/method/raven.api.raven_message.send_message"
    
    # Get from browser dev tools when you send message manually in Raven
    headers = {
        "Authorization": "token e9ffc25922df3cd:7f1526485145fda",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Channel ID
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
