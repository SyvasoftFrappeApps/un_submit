import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 100},
        {"label": "Sales Rep", "fieldname": "sales_person", "fieldtype": "Data", "width": 150},
        {"label": "Total Sales", "fieldname": "total", "fieldtype": "Currency", "width": 120},
    ]

    data = get_data(filters)
    return columns, data

def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("month"):
        months = tuple(filters.get("month"))
        conditions += " AND DATE_FORMAT(si.posting_date, '%%Y-%%m') IN %(months)s"
        values["months"] = months

    return frappe.db.sql("""
        SELECT 
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
            sp.sales_person AS sales_person,
            SUM(si.base_net_total) AS total
        FROM `tabSales Invoice` si
        JOIN `tabSales Team` sp ON sp.parent = si.name
        WHERE si.docstatus = 1 {conditions}
        GROUP BY month, sales_person
        ORDER BY month DESC, sales_person ASC
    """.format(conditions=conditions), values, as_dict=True)
