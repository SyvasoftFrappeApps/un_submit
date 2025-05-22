import frappe
from un_submit.setup.data.permlevel_property_setter import config
from un_submit.utils.style import TerminalColors

def create_permlevel_property_setters(property_setters_permlevel):
    for doc_type, permlevel_data in property_setters_permlevel.items():
        for permlevel, fieldnames in permlevel_data.items():
            for fieldname in fieldnames:
                try:
                    if not frappe.db.exists("Property Setter", {
                        "doc_type": doc_type,
                        "field_name": fieldname,
                        "property": "permlevel"
                    }):
                        # Create the property setter document
                        property_setter_doc = frappe.get_doc({
                            "doctype": "Property Setter",
                            "doc_type": doc_type,
                            "field_name": fieldname,
                            "property": "permlevel",
                            "property_type": "Int",
                            "value": permlevel,
                            "doctype_or_field": "DocField"
                        })
                        
                        property_setter_doc.insert()
                        frappe.db.commit()

                        print(f"{TerminalColors.GREEN}Permlevel Property Setter created for {doc_type} - {fieldname} (permlevel: {permlevel}){TerminalColors.RESET}")
                    else:
                        print(f"{TerminalColors.YELLOW}Permlevel Property Setter already exists for {doc_type} - {fieldname}{TerminalColors.RESET}")
                except Exception as e:
                    print(f"{TerminalColors.RED}Error creating Permlevel Property Setter for {doc_type} - {fieldname}:\n{str(e)}{TerminalColors.RESET}")

def delete_permlevel_property_setters(property_setters_permlevel):
    for doc_type, permlevel_data in property_setters_permlevel.items():
        for permlevel, fieldnames in permlevel_data.items():
            for fieldname in fieldnames:
                try:
                    filters = {
                        "doc_type": doc_type,
                        "field_name": fieldname,
                        "property": "permlevel"
                    }

                    # Fetch matching property setters
                    property_setters = frappe.get_all("Property Setter", filters=filters)

                    for setter in property_setters:
                        try:
                            frappe.delete_doc("Property Setter", setter.name)
                            frappe.db.commit()
                            print(f"{TerminalColors.GREEN}Permlevel Property Setter deleted for {doc_type} - {fieldname}{TerminalColors.RESET}")
                        except Exception as e:
                            print(f"{TerminalColors.RED}Error deleting Permlevel Property Setter for {doc_type} - {fieldname}:\n{str(e)}{TerminalColors.RESET}")
                except Exception as e:
                    print(f"{TerminalColors.RED}Error processing deletion for {doc_type} - {fieldname}:\n{str(e)}{TerminalColors.RESET}")

def install_permlevel_property_setters():
    create_permlevel_property_setters(config)

def uninstall_permlevel_property_setters():
    delete_permlevel_property_setters(config)