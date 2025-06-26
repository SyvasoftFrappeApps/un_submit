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
   message = (
    f"🛑 Sales Order Blocked Due to Overdue!\n"
    f"\n"
    f"Sales Order     : {doc.name}\n\n"
    f"Customer        : {doc.customer_name}\n\n"
    f"Created By      : {doc.owner}\n\n"
    f"Date            : {doc.creation.strftime('%Y-%m-%d')}\n\n"
    f"\n"
    f"👉 Next Actions:\n\n"
    f"📝 Submit Justification: {justification_url}\n\n"
    f"❌ Cancel Order: {cancel_url}"
)


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
