import frappe
from un_submit.setup.data.custom_field import config
from un_submit.utils.style import TerminalColors

# Create custom fields
def create_custom_field(custom_fields):
    for doctype, fields in custom_fields.items():
        for field in fields:
            label = field.get('label', '')

            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field['fieldname']}):
                try:
                    custom_field = frappe.get_doc({
                        "doctype": "Custom Field",
                        "dt": doctype,
                        "fieldname": field['fieldname'],
                        "label": label if field['fieldtype'] not in ['Column Break'] else None,
                        "fieldtype": field['fieldtype'],
                        "insert_after": field.get("insert_after"),
                        "fetch_from": field.get("fetch_from"),
                        "precision": field.get("precision"),
                        "reqd": field.get("reqd", 0),
                        "read_only": field.get("read_only", 0),
                        "hidden": field.get("hidden", 0),
                        "options": field.get("options"),
                        "collapsible": field.get("collapsible", 0),
                        "in_list_view": field.get("in_list_view", 0),
                        "in_standard_filter": field.get("in_standard_filter", 0),
                        "default": field.get("default"),
                        "depends_on": field.get("depends_on"),
                        "read_only_depends_on": field.get("read_only_depends_on"),
                        "bold": field.get("bold", 0),
                        "no_copy": field.get("no_copy", 0),
                        "unique": field.get("unique", 0),
                        "translatable": field.get("translatable", 0),
                        "ignore_user_permissions": field.get("ignore_user_permissions", 0),
                        "description": field.get("description"),
                        "in_global_search": field.get("in_global_search", 0),
                        "link_filters": field.get("link_filters"),
                        "non_negative": field.get("non_negative", 0),
                        "in_preview" : field.get("in_preview", 0)
                    })
                    custom_field.insert()
                    print(f"{TerminalColors.GREEN}Successfully created field '{field['fieldname']}' in {doctype} DocType.{TerminalColors.RESET}")
                except Exception as e:
                    print(f"{TerminalColors.RED}An error occurred while creating '{field['fieldname']}' field in {doctype} DocType.\nError details: {str(e)}{TerminalColors.RESET}")
            else:
                print(f"{TerminalColors.YELLOW}'{field['fieldname']}' Field already exists in {doctype} DocType.{TerminalColors.RESET}")

# Delete custom fields
def delete_custom_field(custom_fields):
    for doctype, fields in custom_fields.items():
        for field in fields:
            
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field['fieldname']}):
                try:
                    frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": field['fieldname']})
                    print(f"{TerminalColors.GREEN}Successfully Deleted field '{field['fieldname']}' in {doctype} DocType. {TerminalColors.RESET}")
                except Exception as e:
                    print(f"{TerminalColors.RED}An error occurred while deleting '{field['fieldname']}' field in '{doctype}' DocType.\nError details: {str(e)}{TerminalColors.RESET}")
            else:
                print(f"{TerminalColors.YELLOW}'{field['fieldname']}' Field does not exist in {doctype} DocType.{TerminalColors.RESET}")

# Install custom fields
def install_custom_fields():
    create_custom_field(config)

# Uninstall custom fields
def uninstall_custom_fields():
    delete_custom_field(config)