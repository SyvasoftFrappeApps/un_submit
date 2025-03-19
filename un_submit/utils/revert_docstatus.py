import frappe

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
