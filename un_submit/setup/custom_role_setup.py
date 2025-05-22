import frappe
from un_submit.utils.style import TerminalColors
from un_submit.setup.data.roles import config

def create_role(custom_roles):
    for role in custom_roles:
        try:
            # Check if the custom role already exists
            if not frappe.db.exists("Role", role):
                role_doc = frappe.get_doc({
                    "doctype": "Role",
                    "role_name": role
                })
                role_doc.insert()
                frappe.db.commit()

                # Log success with green color
                print(f"{TerminalColors.GREEN}Custom role '{role}' created successfully.{TerminalColors.RESET}")
            else:
                print(f"{TerminalColors.YELLOW}Custom role '{role}' already exists.{TerminalColors.RESET}")
        
        except Exception as e:
            # Log error with red color
            print(f"{TerminalColors.RED}Error creating custom role '{role}':\n{str(e)}{TerminalColors.RESET}")

def delete_role(custom_roles):
    for role in custom_roles:
        try:
            # Check if the custom role exists
            if frappe.db.exists("Role", role):
                frappe.delete_doc("Role", role)
                frappe.db.commit()

                # Log success with green color
                print(f"{TerminalColors.GREEN}Custom role '{role}' deleted successfully.{TerminalColors.RESET}")
            else:
                print(f"{TerminalColors.YELLOW}Custom role '{role}' does not exist.{TerminalColors.RESET}")
        
        except Exception as e:
            # Log error with red color
            print(f"{TerminalColors.RED}Error deleting custom role '{role}':\n{str(e)}{TerminalColors.RESET}")

def install_roles():
    create_role(config)

def uninstall_roles():
    delete_role(config)