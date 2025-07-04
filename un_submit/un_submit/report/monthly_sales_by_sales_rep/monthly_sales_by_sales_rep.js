frappe.query_reports["Monthly Sales by Sales Rep"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": "Month (YYYY-MM)",
			"fieldtype": "MultiSelect",
			"get_data": function (txt) {
				return frappe.db.get_list('Sales Invoice', {
					fields: ["posting_date"],
					filters: {
						docstatus: 1
					},
					limit: 1000
				}).then(res => {
					let months = new Set();
					res.forEach(r => {
						let date = frappe.datetime.str_to_obj(r.posting_date);
						let formatted = frappe.datetime.obj_to_str(new Date(date.getFullYear(), date.getMonth(), 1)).slice(0, 7);
						months.add(formatted);
					});
					return [...months].sort().map(m => ({ value: m, label: m }));
				});
			}
		}
	]
};
