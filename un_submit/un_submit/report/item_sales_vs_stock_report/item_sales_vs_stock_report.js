// Copyright (c) 2025, SyvaSoft Business Solutions Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Item Sales vs Stock Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "item_group",
			"label": "Item Group",
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse"
		}
	]
};
