import frappe
from frappe.query_builder import DocType

@frappe.whitelist()
def revert_docstatus(doctype, name):
    """
    Toggle the docstatus of a document and its child records between Draft (0) and Submitted (1)
    using raw SQL. When reverting to Draft, also set the custom field 'ignore_permissions' to 1.
    
    :param doctype: The main document type (e.g., "Purchase Receipt").
    :param name: The name (ID) of the document.
    """
    # Get the document to check current status
    doc = frappe.get_doc(doctype, name)
    new_docstatus = 0 if doc.docstatus == 1 else 1

    # Update the main document using raw SQL.
    # If reverting to Draft, also set ignore_permissions to 1.
    if new_docstatus == 0:
        frappe.db.sql(
            """UPDATE `tab{doctype}` 
               SET docstatus = %s, ignore_permissions = 1 
               WHERE name = %s""".format(doctype=doctype),
            (new_docstatus, name)
        )
    else:
        frappe.db.sql(
            """UPDATE `tab{doctype}` 
               SET docstatus = %s 
               WHERE name = %s""".format(doctype=doctype),
            (new_docstatus, name)
        )

    # Loop through all child table fields in the document.
    for table_field in doc.meta.get_table_fields():
        children = doc.get(table_field.fieldname)
        if children:
            # Assuming all children in this table belong to the same child doctype.
            child_doctype = children[0].doctype
            # Update all child rows for this child table where the parent equals the main doc name.
            frappe.db.sql(
                """UPDATE `tab{child_doctype}` 
                   SET docstatus = %s 
                   WHERE parent = %s""".format(child_doctype=child_doctype),
                (new_docstatus, name)
            )

    frappe.db.commit()
    action = "reverted to Draft" if new_docstatus == 0 else "submitted successfully"
    return {"success": True, "message": f"Document and its child table rows {action}."}



@frappe.whitelist()
def set_purchase_invoice(docname, purchase_invoice):
    """Set Purchase Invoice in all Purchase Receipt Items using Query Builder"""
    
    try:
        PurchaseReceiptItem = DocType("Purchase Receipt Item")

        # Update all Purchase Receipt Items linked to the given Purchase Receipt
        (
            frappe.qb.update(PurchaseReceiptItem)
            .set(PurchaseReceiptItem.purchase_invoice, purchase_invoice)
            .where(PurchaseReceiptItem.parent == docname)
        ).run()

        frappe.db.commit()

        frappe.msgprint(
            msg="Purchase Invoice updated successfully.",
            title="Success",
            indicator="green"
        )
        return "success"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Purchase Invoice Update Error")
        return "error"


@frappe.whitelist()
def toggle_ignore_link_sql(doctype, docname):
    # Check the field exists in the doctype
    if not frappe.db.has_column(doctype, "ignore_linked_document"):
        frappe.throw(f"Field 'ignore_linked_document' not found in {doctype}")

    # Fetch current value
    current_value = frappe.db.get_value(doctype, docname, "ignore_linked_document")

    # Toggle value: 1 becomes 0, 0 becomes 1
    new_value = 0 if current_value else 1

    # Update using SQL
    frappe.db.sql(
        f"UPDATE `tab{doctype}` SET ignore_linked_document = %s WHERE name = %s",
        (new_value, docname)
    )
    frappe.db.commit()

    return {
        "status": "Toggled",
        "new_value": new_value
    }
