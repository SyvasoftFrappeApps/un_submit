import frappe
from frappe.utils import cint, flt, get_datetime, getdate, nowdate

def custom_validate_duplicate_serial_and_batch_bundle(self, table_name):
		if not self.get(table_name):
			return

		sbb_list = []
		for item in self.get(table_name):
			if item.get("serial_and_batch_bundle"):
				sbb_list.append(item.get("serial_and_batch_bundle"))

			if item.get("rejected_serial_and_batch_bundle"):
				sbb_list.append(item.get("rejected_serial_and_batch_bundle"))

		if sbb_list:
			SLE = frappe.qb.DocType("Stock Ledger Entry")
			data = (
				frappe.qb.from_(SLE)
				.select(SLE.voucher_type, SLE.voucher_no, SLE.serial_and_batch_bundle)
				.where(
					(SLE.docstatus == 1)
					& (SLE.serial_and_batch_bundle.notnull())
					& (SLE.serial_and_batch_bundle.isin(sbb_list))
				)
				.limit(1)
			).run(as_dict=True)

			if data:
				data = data[0]
				if self.ignore_permissions == 0:
					frappe.throw(
						_("Serial and Batch Bundle {0} is already used in {1} {2}.").format(
							frappe.bold(data.serial_and_batch_bundle), data.voucher_type, data.voucher_no
						)
					)

def custom_validate_with_previous_doc(self):
		if self.ignore_permissions == 0:	
			super().validate_with_previous_doc(
				{
					"Purchase Order": {
						"ref_dn_field": "purchase_order",
						"compare_fields": [["supplier", "="], ["company", "="], ["currency", "="]],
					},
					"Purchase Order Item": {
						"ref_dn_field": "purchase_order_item",
						"compare_fields": [["project", "="], ["uom", "="], ["item_code", "="]],
						"is_child_table": True,
						"allow_duplicate_prev_row_id": True,
					},
				}
			)

		if (
			cint(frappe.db.get_single_value("Buying Settings", "maintain_same_rate"))
			and not self.is_return
			and not self.is_internal_supplier
		):
			self.validate_rate_with_reference_doc(
				[["Purchase Order", "purchase_order", "purchase_order_item"]]
			)
		
def custom_validate_rate_with_reference_doc(self, ref_details):
		if self.get("is_internal_supplier"):
			return

		buying_doctypes = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]

		if self.doctype in buying_doctypes:
			action, role_allowed_to_override = frappe.get_cached_value(
				"Buying Settings", "None", ["maintain_same_rate_action", "role_to_override_stop_action"]
			)
		else:
			action, role_allowed_to_override = frappe.get_cached_value(
				"Selling Settings", "None", ["maintain_same_rate_action", "role_to_override_stop_action"]
			)

		stop_actions = []
		for ref_dt, ref_dn_field, ref_link_field in ref_details:
			reference_names = [d.get(ref_link_field) for d in self.get("items") if d.get(ref_link_field)]
			reference_details = self.get_reference_details(reference_names, ref_dt + " Item")
			for d in self.get("items"):
				if d.get(ref_link_field):
					ref_rate = reference_details.get(d.get(ref_link_field))

					if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= 0.01:
						if self.ignore_permissions == 0:
							if action == "Stop":
								if role_allowed_to_override not in frappe.get_roles():
									stop_actions.append(
										_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4})").format(
											d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate
										)
									)
							else:
								frappe.msgprint(
									_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4})").format(
										d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate
									),
									title=_("Warning"),
									indicator="orange",
								)
		if stop_actions:
			frappe.throw(stop_actions, as_list=True)