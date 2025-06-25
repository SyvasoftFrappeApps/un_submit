import frappe
from frappe.utils import now_datetime, get_fullname
from raven.raven import send_raven_notification

@frappe.whitelist()
def send_overdue_notification(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)

    # Call the same credit control logic
    from un_submit.credit_control.credit_control import check_overdue_for_customer
    result = check_overdue_for_customer(doc.customer, doc.name)

    if not result.get("is_blocked"):
        return

    # Message formatting
    created_user = get_fullname(doc.owner)
    created_date = doc.creation.strftime("%d-%b-%Y %I:%M %p")
    message = f"""
⚠️ *Overdue Sales Order Blocked*

*Sales Order:* {doc.name}  
*Customer:* {doc.customer_name}  
*Created By:* {created_user}  
*Created On:* {created_date}  
*Overdue Amount:* ₹ {result.get("overdue_amount", 0):,.2f}  
*Overdue Days:* {result.get("overdue_days")}  

Please review and take action.
"""

    # Buttons for action (you can link to a custom form view or page)
    buttons = [
        {
            "label": "➕ Justify & Proceed",
            "type": "link",
            "url": f"/app/sales-order/{doc.name}"
        },
        {
            "label": "❌ Cancel Order",
            "type": "custom",
            "action": "frappe.call({method: 'un_submit.credit_control.sales_order.cancel_order', args: { sales_order: '%s' }})" % doc.name
        }
    ]

    # Send to channel or user
    send_raven_notification(
        users=None,  # optional if you're using a channel
        channel="general",  # set this in Raven setup
        message=message.strip(),
        subject=f"Overdue Alert: {doc.name}",
        doctype="Sales Order",
        name=doc.name,
        actions=buttons
    )


@frappe.whitelist()
def cancel_order(sales_order):
    doc = frappe.get_doc("Sales Order", sales_order)
    if doc.docstatus == 0:
        doc.cancel()
        return "Order cancelled."
    else:
        frappe.throw("Order already submitted or already cancelled.")