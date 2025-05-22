import frappe
from un_submit.utils.style import TerminalColors
from un_submit.setup.data.property_setter import config

def create_property_setters(property_setters):
    for setter in property_setters:
        try:
            # Check if field_name exists; use None if missing
            field_name = setter.get('field_name', None)
            
            if not frappe.db.exists("Property Setter", {
                "doc_type": setter["doc_type"], 
                "field_name": field_name,  # Use field_name variable
                "property": setter["property"]
            }):
                property_setter_doc = frappe.get_doc({
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField" if field_name else "DocType",  # Adjust based on presence of field_name
                    **setter
                })
                
                property_setter_doc.insert()
                frappe.db.commit()

                print(f"{TerminalColors.GREEN}Property Setter created for {setter['doc_type']} - {field_name or 'Doctype-level'}{TerminalColors.RESET}")
            else:
                print(f"{TerminalColors.YELLOW}Property Setter already exists for {setter['doc_type']} - {field_name or 'Doctype-level'}{TerminalColors.RESET}")
        
        except Exception as e:
            print(f"{TerminalColors.RED}Error creating Property Setter for {setter['doc_type']} - {field_name or 'Doctype-level'}:\n{str(e)}{TerminalColors.RESET}")


def delete_property_setters(property_setters):
    for setter in property_setters:
        try:
            # Safely get the field_name or use None if it doesn't exist
            field_name = setter.get("field_name", None)
            
            # Prepare filters
            filters = {"doc_type": setter["doc_type"]}
            if field_name:
                filters["field_name"] = field_name
            
            # Fetch matching property setters
            property_setter = frappe.get_all("Property Setter", filters=filters)

            for setter_doc in property_setter:
                try:
                    frappe.delete_doc("Property Setter", setter_doc.name)
                    frappe.db.commit()
                    
                    print(f"{TerminalColors.GREEN}Property Setter deleted for {setter['doc_type']} - {field_name or 'Doctype-level'}{TerminalColors.RESET}")
                except Exception as e:
                    print(f"{TerminalColors.RED}Error deleting Property Setter for {setter['doc_type']} - {field_name or 'Doctype-level'}:\n{str(e)}{TerminalColors.RESET}")
        except Exception as e:
            print(f"{TerminalColors.RED}Error in processing Property Setter deletion for {setter['doc_type']} - {field_name or 'Doctype-level'}:\n{str(e)}{TerminalColors.RESET}")


def install_property_setter():
    create_property_setters(config)

def uninstall_property_setter():
    delete_property_setters(config)