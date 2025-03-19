import frappe

@frappe.whitelist()
def revert_docstatus(doctype, name):
    """
    Toggle the docstatus of a document and its child records between Draft (0) and Submitted (1).
    
    :param doctype: The main document type (e.g., "Purchase Receipt").
    :param name: The name (ID) of the document.
    """
    doc = frappe.get_doc(doctype, name)

    # Determine the new docstatus (toggle between 0 and 1)
    new_docstatus = 0 if doc.docstatus == 1 else 1
    if  new_docstatus == 0:
        frappe.db.set_value(doctype, name, "ignore_permissions", 1)

    # Update the main document's docstatus
    frappe.db.set_value(doctype, name, "docstatus", new_docstatus)
    

    # Loop through all child tables and update their docstatus
    for table_field in doc.meta.get_table_fields():
        if doc.get(table_field.fieldname):
            for child in doc.get(table_field.fieldname):
                if hasattr(child, 'docstatus') and child.docstatus != new_docstatus:
                    frappe.db.set_value(child.doctype, child.name, "docstatus", new_docstatus)

    frappe.db.commit()

    action = "reverted to Draft" if new_docstatus == 0 else "submitted successfully"
    return {"success": True, "message": f"Document and its child table rows {action}."}
