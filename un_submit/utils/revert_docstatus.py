import frappe

@frappe.whitelist()
def revert_docstatus(doctype, name):
    doc = frappe.get_doc(doctype, name)
    
    if doc.docstatus == 1:  # Ensure the main document is submitted
        # Revert the main document to draft
        frappe.db.set_value(doctype, name, "docstatus", 0)
        
        # Loop through all child table fields in the document
        for table_field in doc.meta.get_table_fields():
            if doc.get(table_field.fieldname):
                for child in doc.get(table_field.fieldname):
                    # If the child document has a docstatus and is submitted, revert it to draft
                    if hasattr(child, 'docstatus') and child.docstatus == 1:
                        frappe.db.set_value(child.doctype, child.name, "docstatus", 0)
                        
        frappe.db.commit()
        return {"success": True, "message": "Document and its child table rows reverted to Draft"}
    
    return {"success": False, "message": "Document is not in a submitted state"}
