import frappe

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)

    # Example logic — replace with your actual overdue check
    overdue_amount = 12345
    overdue_days = 60

    justification_url = frappe.utils.get_url(f"/app/sales-order/{doc.name}#justification")
    cancel_url = frappe.utils.get_url(
        f"/api/method/un_submit.credit_control.cancel_order?sales_order={doc.name}"
    )

    # Compose the full message
    full_message = f"""
🛑 *Sales Order Blocked Due to Overdue!*

```plaintext
| Field           | Value                            |
|----------------|----------------------------------|
| Sales Order     | {doc.name}                       |
| Customer        | {doc.customer_name}              |
| Created By      | {doc.owner}                      |
| Date            | {doc.creation.strftime('%Y-%m-%d')} |
| Overdue Amount  | ₹{overdue_amount}                |
| Overdue Days    | {overdue_days}                   |
👉 Next Actions:

📝 Submit Justification: {justification_url}

❌ Cancel Order: {cancel_url}
"""
frappe.get_doc({
"doctype": "Raven Message",
"channel_id": "general",
"text": full_message,
"message_type": "Text"
}).insert(ignore_permissions=True)

return "Notification sent successfully."