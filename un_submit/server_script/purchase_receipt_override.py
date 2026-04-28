import frappe
import json
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
			if getattr(self, "ignore_permissions", None) == 0:
				frappe.throw(
					_("Serial and Batch Bundle {0} is already used in {1} {2}.").format(
						frappe.bold(data.serial_and_batch_bundle), data.voucher_type, data.voucher_no
					)
				)

def custom_validate_with_previous_doc(self, *args, **kwargs):
	pass

		
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

				# Guard against None when item has no reference doc link
				if ref_rate is None:
					frappe.msgprint(
						_("Row #{0}: No reference rate found for item {1}. Rate validation skipped.").format(
							d.idx, d.item_code
						),
						title=_("Warning"),
						indicator="orange",
					)
					continue

				if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= 0.01:
					if getattr(self, "ignore_permissions", None) == 0:
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

def transaction_validate_with_previous_doc(self, ref):
	if getattr(self, "ignore_permissions", None) == 0:
		self.exclude_fields = ["conversion_factor", "uom"] if self.get("is_return") else []

		for key, val in ref.items():
			is_child = val.get("is_child_table")
			ref_doc = {}
			item_ref_dn = []
			for d in self.get_all_children(self.doctype + " Item"):
				ref_dn = d.get(val["ref_dn_field"])
				if ref_dn:
					if is_child:
						self.compare_values({key: [ref_dn]}, val["compare_fields"], d)
						if ref_dn not in item_ref_dn:
							item_ref_dn.append(ref_dn)
						elif not val.get("allow_duplicate_prev_row_id"):
							frappe.throw(_("Duplicate row {0} with same {1}").format(d.idx, key))
					elif ref_dn:
						ref_doc.setdefault(key, [])
						if ref_dn not in ref_doc[key]:
							ref_doc[key].append(ref_dn)
			if ref_doc:
				self.compare_values(ref_doc, val["compare_fields"])

from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import execute_repost_item_valuation

@frappe.whitelist()
def after_submit_purchase_receipt(doc, method):
	# Convert doc to a dictionary if it is a JSON string
	if isinstance(doc, str):
		doc = json.loads(doc)

	# Ensure the purchase receipt is not ignoring permissions
	if doc.get("ignore_permissions") == 1:
		try:
			# Create a new Repost Item Valuation
			repost_doc = frappe.get_doc({
				"doctype": "Repost Item Valuation",
				"based_on": "Transaction",
				"voucher_type": "Purchase Receipt",
				"voucher_no": doc.get("name")
			})

			# Insert and Submit the document
			repost_doc.insert()
			repost_doc.submit()

			# Manually execute the reposting function
			frappe.get_doc("Scheduled Job Type", "repost_item_valuation.repost_entries").enqueue(force=True)

			frappe.msgprint(f"Repost Item Valuation created for {doc.get('name')}")

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Repost Item Valuation Error")