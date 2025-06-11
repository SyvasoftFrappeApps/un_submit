# Copyright (c) 2025
# License: MIT. See license.txt

import frappe

def execute(filters=None):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw("Please select both From Date and To Date")

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": "On Hand Qty", "fieldname": "on_hand_qty", "fieldtype": "Float", "width": 120},
        {"label": "Sold Qty", "fieldname": "sold_qty", "fieldtype": "Float", "width": 100},
        {"label": "Custom Qty (Ratio)", "fieldname": "custom_qty", "fieldtype": "Float", "width": 130},
        {"label": "Apple ID", "fieldname": "apple_id", "fieldtype": "Data", "width": 130},
    ]

def get_data(filters):
    conditions = ""
    values = filters.copy()

    # Handle item_group MultiSelect
    if filters.get("item_group"):
        item_groups = tuple(filters["item_group"])
        conditions += " AND item.item_group IN %(item_groups)s"
        values["item_groups"] = item_groups

    if filters.get("warehouse"):
        conditions += " AND bin.warehouse = %(warehouse)s"

    if filters.get("apple_id") == "Yes":
        conditions += " AND tc.apple_id IS NOT NULL AND tc.apple_id != ''"
    elif filters.get("apple_id") == "No":
        conditions += " AND (tc.apple_id IS NULL OR tc.apple_id = '')"


    return frappe.db.sql(f"""
        SELECT
            item.item_code,
            item.item_name,
            item.item_group,
            bin.warehouse,
            SUM(IFNULL(bin.actual_qty, 0)) AS on_hand_qty,
            SUM(IF(si.posting_date BETWEEN %(from_date)s AND %(to_date)s, si_item.qty, 0)) AS sold_qty,
            ROUND(
                (SUM(IFNULL(bin.actual_qty, 0)) / NULLIF(SUM(IF(si.posting_date BETWEEN %(from_date)s AND %(to_date)s, si_item.qty, 0)), 0)),
                2
            ) AS custom_qty,
            IF(MAX(tc.apple_id) IS NOT NULL AND MAX(tc.apple_id) != '', 'Yes', 'No') AS apple_id
        FROM
            tabItem item
        LEFT JOIN tabBin bin ON bin.item_code = item.item_code
        LEFT JOIN `tabSales Invoice Item` si_item ON si_item.item_code = item.item_code
        LEFT JOIN `tabSales Invoice` si ON si.name = si_item.parent AND si.docstatus = 1
        LEFT JOIN tabCustomer tc ON tc.name = si.customer
        WHERE 1=1 {conditions}
        GROUP BY
            item.item_code, item.item_name, item.item_group, bin.warehouse
        HAVING
            on_hand_qty > 0
        ORDER BY
            on_hand_qty DESC
    """, values, as_dict=True)
