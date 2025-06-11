# Copyright (c) 2013, Mohammad Ali and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import date_diff


def execute(filters):
	columns, data = [], []
	frappe.log_error("filters", filters)

	columns = [
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 180
		},
		{
			"label": _("Apple ID"),
			"fieldname": "apple_id",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 180
		},
		{
			"label": _("Sales Invoice Date"),
			"fieldname": "si_date",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"label": _("Total Bill Amount"),
			"fieldname": "total_bill_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Allocated Amount"),
			"fieldname": "allocated_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Total Outstanding"),
			"fieldname": "total_outstanding",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Payment Entry"),
			"fieldname": "payment_entry",
			"fieldtype": "Link",
			"options": "Payment Entry",
			"width": 180
		},
		{
			"label": _("Cheque Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Outstanding Days"),
			"fieldname": "outstanding_days",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Cheque Days"),
			"fieldname": "cheque_days",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Cheque Ref. No."),
			"fieldname": "ref_no",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Cheque Ref. Date"),
			"fieldname": "ref_date",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"label": _("PE Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 150
		}
	]

	data = get_data(filters)
	return columns, data


def get_data(filters=None):
	filters = frappe._dict(filters or {})
	data = []

	conditions = ""
	if filters.from_date and filters.to_date:
		conditions += f" and tsi.posting_date between '{filters.get('from_date')}' and '{filters.get('to_date')}' "

	get_customer_list = []
	if filters.get("customer"):
		for d in filters.get("customer"):
			frappe.log_error("customer", d)
			get_customer_list.append({"customer": d})
	else:
		get_customer_list = frappe.db.sql("""
			SELECT customer FROM `tabSales Invoice`
			WHERE outstanding_amount > 0 AND status != 'Return'
			GROUP BY customer
		""", as_dict=1)

	if get_customer_list:
		for cust in get_customer_list:
			customer = cust.customer
			apple_id_val = frappe.db.get_value("Customer", customer, "apple_id")
			apple_id_status = "Yes" if apple_id_val else "No"

			# Skip customers if Apple ID filter is set and doesn't match
			if filters.get("apple_id") and filters.apple_id != apple_id_status:
				continue


			pe_list_invoice = frappe.db.sql(f"""
				SELECT
					tsi.customer AS customer,
					tsi.posting_date AS si_date,
					tsi.name AS si_name,
					tsi.status AS ref_status,
					tsi.rounded_total AS total_amount,
					tsi.outstanding_amount AS outstanding_amount
				FROM `tabSales Invoice` tsi
				WHERE tsi.outstanding_amount > 0 AND tsi.docstatus <= 1
					AND tsi.status != 'Return' AND tsi.customer = %s
					{conditions}
				ORDER BY tsi.posting_date ASC
			""", (customer,), as_dict=True)

			customer_total_outstanding = 0.0

			for pe in pe_list_invoice:
				outstanding_days = (frappe.utils.now_datetime().date() - pe.si_date).days

				if filters.get("payment_entry") == "Yes":
					payment_entries = frappe.db.get_all(
						"Payment Entry Reference",
						filters={"reference_name": pe.si_name, "reference_doctype": "Sales Invoice"},
						fields=["parent", "allocated_amount", "outstanding_amount", "total_amount"]
					)

					for pe_e in payment_entries:
						payment_entry_doc = frappe.db.get_value(
							"Payment Entry", {"name": pe_e.parent},
							["paid_amount", "reference_date", "reference_no", "workflow_state"], as_dict=True
						)

						cheque_days = (payment_entry_doc.reference_date - pe.si_date).days if payment_entry_doc.reference_date else 0

						data.append({
							"customer": pe.customer,
							"apple_id": apple_id_status,
							"sales_invoice": pe.si_name,
							"si_date": pe.si_date,
							"total_bill_amount": pe.total_amount,
							"allocated_amount": pe_e.allocated_amount or 0,
							"total_outstanding": pe.outstanding_amount,
							"payment_entry": pe_e.parent,
							"paid_amount": payment_entry_doc.paid_amount or 0,
							"outstanding_days": outstanding_days,
							"cheque_days": cheque_days,
							"ref_no": payment_entry_doc.reference_no,
							"ref_date": payment_entry_doc.reference_date,
							"status": payment_entry_doc.workflow_state
						})

				elif filters.get("payment_entry") == "No":
					data.append({
						"customer": pe.customer,
						"apple_id": apple_id_status,
						"sales_invoice": pe.si_name,
						"si_date": pe.si_date,
						"total_bill_amount": pe.total_amount,
						"allocated_amount": 0,
						"total_outstanding": pe.outstanding_amount,
						"payment_entry": "",
						"paid_amount": 0,
						"outstanding_days": outstanding_days,
						"cheque_days": 0,
						"ref_no": "",
						"ref_date": "",
						"status": ""
					})

				else:  # if no filter or None
					payment_entries = frappe.db.get_all(
						"Payment Entry Reference",
						filters={"reference_name": pe.si_name, "reference_doctype": "Sales Invoice"},
						fields=["parent", "allocated_amount", "outstanding_amount", "total_amount"]
					)

					if payment_entries:
						for pe_e in payment_entries:
							payment_entry_doc = frappe.db.get_value(
								"Payment Entry", {"name": pe_e.parent},
								["paid_amount", "reference_date", "reference_no", "workflow_state"], as_dict=True
							)
							cheque_days = (payment_entry_doc.reference_date - pe.si_date).days if payment_entry_doc.reference_date else 0

							data.append({
								"customer": pe.customer,
								"apple_id": apple_id_status,
								"sales_invoice": pe.si_name,
								"si_date": pe.si_date,
								"total_bill_amount": pe.total_amount,
								"allocated_amount": pe_e.allocated_amount or 0,
								"total_outstanding": pe.outstanding_amount,
								"payment_entry": pe_e.parent,
								"paid_amount": payment_entry_doc.paid_amount or 0,
								"outstanding_days": outstanding_days,
								"cheque_days": cheque_days,
								"ref_no": payment_entry_doc.reference_no,
								"ref_date": payment_entry_doc.reference_date,
								"status": payment_entry_doc.workflow_state
							})
					else:
						data.append({
							"customer": pe.customer,
							"apple_id": apple_id_status,
							"sales_invoice": pe.si_name,
							"si_date": pe.si_date,
							"total_bill_amount": pe.total_amount,
							"allocated_amount": 0,
							"total_outstanding": pe.outstanding_amount,
							"payment_entry": "",
							"paid_amount": 0,
							"outstanding_days": outstanding_days,
							"cheque_days": 0,
							"ref_no": "",
							"ref_date": "",
							"status": ""
						})

				customer_total_outstanding += pe.outstanding_amount

			if customer_total_outstanding > 0:
				data.append({
					"customer": customer,
					"apple_id": apple_id_status,
					"total_outstanding": customer_total_outstanding
				})
				data.append({
					"customer": "",
					"apple_id": "",
					"total_outstanding": ""
				})

	frappe.log_error("customerlist", get_customer_list)
	return data
