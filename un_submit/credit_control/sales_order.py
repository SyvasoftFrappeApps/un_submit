import requests
import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)

    # Replace with actual overdue values from your logic
    overdue_amount = "25,000"
    overdue_days = "45"

    base_url = frappe.utils.get_url()
    sales_order_url = f"{base_url}/app/sales-order/{doc.name}"
    justification_url = f"{sales_order_url}#justification"
    cancel_url = f"{base_url}/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"

    # Properly formatted message using plain text
    message = """
🛑 Sales Order Blocked Due to Overdue!

Sales Order     : {}
Customer        : {}
Created By      : {}
Date            : {}


👉 Next Actions:
📝 Submit Justification: {}
❌ Cancel Order: {}
""".format(doc.name, doc.customer_name, doc.owner, doc.creation.strftime('%Y-%m-%d'), justification_url, cancel_url)


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
