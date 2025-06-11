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
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "MultiSelectList",
			options: "Item Group",
			get_data: function (txt) {
				return frappe.db.get_link_options("Item Group");
			},
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "apple_id",
			"label": "Apple ID",
			"fieldtype": "Data"
		}
	]
};
