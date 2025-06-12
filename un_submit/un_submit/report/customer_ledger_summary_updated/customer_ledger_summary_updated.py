# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, qb, scrub
from frappe.query_builder import Criterion, Tuple
from frappe.query_builder.functions import IfNull
from frappe.utils import getdate, nowdate, add_days
from frappe.utils.nestedset import get_descendants_of
from pypika.terms import LiteralValue
from pypika.functions import Count, Sum
from pypika import CustomFunction  # Added for DATEDIFF

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)

TREE_DOCTYPES = frozenset(
	["Customer Group", "Territory", "Supplier Group", "Sales Partner", "Sales Person", "Cost Center"]
)


class PartyLedgerSummaryReport:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.from_date = getdate(self.filters.from_date or nowdate())
		self.filters.to_date = getdate(self.filters.to_date or nowdate())
		# Parse multiple ranges from filters (e.g., "10, 15" or "20, 40, 60")
		self.ranges = [
			int(num.strip()) for num in self.filters.get("avg_outstanding_ranges", "10").split(",")
			if num.strip().isdigit() and int(num.strip()) > 0
		]
		self.ranges = sorted(self.ranges)  # Ensure ranges are sorted
		if not self.ranges:
			frappe.throw(_("Average outstanding ranges must contain at least one valid positive integer"))

	def run(self, args):
		self.filters.party_type = args.get("party_type")
		self.validate_filters()
		self.get_party_details()
		if not self.parties:
			return [], []
		self.get_gl_entries()
		self.get_return_invoices()
		self.get_party_adjustment_amounts()
		self.get_cheque_count()
		self.get_average_outstanding()
		self.party_naming_by = frappe.db.get_single_value(args.get("naming_by")[0], args.get("naming_by")[1])
		columns = self.get_columns()
		data = self.get_data()
		return columns, data

	def get_average_outstanding(self):
		"""Calculate average outstanding for each party over each range."""
		self.avg_outstanding = frappe._dict()
		for party in self.parties:
			self.avg_outstanding[party] = frappe._dict()
			for idx, days_range in enumerate(self.ranges):
				avg_balance = self.get_average_outstanding_for_customer(party, days_range)
				self.avg_outstanding[party][idx] = round(avg_balance, 2)

	def get_average_outstanding_for_customer(self, customer, days_range):
		"""
		Calculate average outstanding for a customer over a given days range.
		Formula: (Current Closing Balance - Invoiced Amount in Range) / day_range
		"""
		gle = qb.DocType("GL Entry")
		customer_table = qb.DocType("Customer")
		invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
		reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"

		# 1. Get Current Closing Balance up to to_date
		closing_balance_query = (
			qb.from_(gle)
			.select(
				Sum(gle[invoice_dr_or_cr] - gle[reverse_dr_or_cr]).as_("balance")
			)
			.where(
				(gle.docstatus < 2)
				& (gle.is_cancelled == 0)
				& (gle.party_type == self.filters.party_type)
				& (IfNull(gle.party, "") != "")
				& (gle.posting_date <= self.filters.to_date)
				& (gle.party == customer)
			)
		)
		closing_balance_query = self.prepare_conditions(closing_balance_query)
		closing_balance = closing_balance_query.run()[0][0] or 0

		# 2. Get Invoiced Amount within the range (to_date - days_range to to_date)
		invoiced_amount_query = (
			qb.from_(gle)
			.left_join(customer_table)
			.on(gle.party == customer_table.name)
			.select(
				Sum(gle.debit).as_("total_invoiced_amount")
			)
			.where(
				(gle.party_type == "Customer")
				& (gle.company == self.filters.company)
				& (gle.is_cancelled == 0)
				& (gle.docstatus < 2)
				& (gle.posting_date.between(
					add_days(self.filters.to_date, -days_range),
					self.filters.to_date
				))
				& (gle.debit > 0)
				& (gle.is_opening == "No")
				& (gle.voucher_type.isin(["Sales Invoice", "Journal Entry"]))
				& (gle.party == customer)
			)
		)
		invoiced_amount = invoiced_amount_query.run()[0][0] or 0

		# 3. Calculate average outstanding
		avg_balance = (closing_balance - invoiced_amount) / days_range if days_range else 0
		return avg_balance

	def validate_filters(self):
		if not self.filters.get("company"):
			frappe.throw(_("{0} is mandatory").format(_("Company")))
		if self.filters.from_date > self.filters.to_date:
			frappe.throw(_("From Date must be before To Date"))
		self.update_hierarchical_filters()

	def update_hierarchical_filters(self):
		for doctype in TREE_DOCTYPES:
			key = scrub(doctype)
			if self.filters.get(key):
				self.filters[key] = get_children(doctype, self.filters[key])

	def get_party_details(self):
		self.parties = []
		self.party_details = frappe._dict()
		party_type = self.filters.party_type
		doctype = qb.DocType(party_type)
		conditions = self.get_party_conditions(doctype)
		query = (
			qb.from_(doctype)
			.select(doctype.name.as_("party"), f"{scrub(party_type)}_name")
			.where(Criterion.all(conditions))
		)
		from frappe.desk.reportview import build_match_conditions
		match_conditions = build_match_conditions(party_type)
		if match_conditions:
			query = query.where(LiteralValue(match_conditions))
		party_details = query.run(as_dict=True)
		for row in party_details:
			self.parties.append(row.party)
			self.party_details[row.party] = row

	def get_cheque_count(self):
		if self.filters.party_type != "Customer":
			return
		self.cheque_counts = frappe._dict()
		for party in self.parties:
			self.cheque_counts[party] = {
				"cheque_received_count": 0,
				"cheque_received_amount": 0.0,
				"cheque_deposited_count": 0,
				"cheque_deposited_amount": 0.0,
			}
		pe = qb.DocType("Payment Entry")
		query = (
			qb.from_(pe)
			.select(
				pe.party,
				pe.workflow_state,
				Count("*").as_("count"),
				Sum(pe.paid_amount).as_("total_amount")
			)
			.where(
				(pe.party_type == self.filters.party_type)
				& (pe.party.isin(self.parties))
				& (pe.workflow_state.isin(["Cheque Received", "Cheque Deposited"]))
				& (pe.posting_date.between(self.filters.from_date, self.filters.to_date))
			)
			.groupby(pe.party, pe.workflow_state)
		)
		results = query.run(as_dict=True)
		for row in results:
			if row.workflow_state == "Cheque Received":
				self.cheque_counts[row.party]["cheque_received_count"] = row["count"]
				self.cheque_counts[row.party]["cheque_received_amount"] = row["total_amount"]
			elif row.workflow_state == "Cheque Deposited":
				self.cheque_counts[row.party]["cheque_deposited_count"] = row["count"]
				self.cheque_counts[row.party]["cheque_deposited_amount"] = row["total_amount"]

	def get_party_conditions(self, doctype):
		conditions = []
		group_field = "customer_group" if self.filters.party_type == "Customer" else "supplier_group"
		if self.filters.party:
			conditions.append(doctype.name == self.filters.party)
		if self.filters.territory:
			conditions.append(doctype.territory.isin(self.filters.territory))
		if self.filters.get(group_field):
			conditions.append(doctype[group_field].isin(self.filters.get(group_field)))
		if self.filters.payment_terms_template:
			conditions.append(doctype.payment_terms == self.filters.payment_terms_template)
		if self.filters.sales_partner:
			conditions.append(doctype.default_sales_partner.isin(self.filters.sales_partner))
		if self.filters.sales_person:
			sales_team = qb.DocType("Sales Team")
			sales_invoice = qb.DocType("Sales Invoice")
			customers = (
				qb.from_(sales_team)
				.select(sales_team.parent)
				.where(sales_team.sales_person.isin(self.filters.sales_person))
				.where(sales_team.parenttype == "Customer")
			) + (
				qb.from_(sales_team)
				.join(sales_invoice)
				.on(sales_team.parent == sales_invoice.name)
				.select(sales_invoice.customer)
				.where(sales_team.sales_person.isin(self.filters.sales_person))
				.where(sales_team.parenttype == "Sales Invoice")
			)
			conditions.append(doctype.name.isin(customers))
		return conditions

	def get_columns(self):
		columns = [
			{
				"label": _(self.filters.party_type),
				"fieldtype": "Link",
				"fieldname": "party",
				"options": self.filters.party_type,
				"width": 200,
			},
			{
				"label": _("Apple ID"),
				"fieldtype": "Data",
				"fieldname": "apple_id",
				"width": 200,
			},
		]
		if self.party_naming_by == "Naming Series":
			columns.append(
				{
					"label": _(self.filters.party_type + " Name"),
					"fieldtype": "Data",
					"fieldname": "party_name",
					"width": 150,
				}
			)
		credit_or_debit_note = "Credit Note" if self.filters.party_type == "Customer" else "Debit Note"
		columns += [
			{
				"label": _("Opening Balance"),
				"fieldname": "opening_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Invoiced Amount"),
				"fieldname": "invoiced_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Paid Amount"),
				"fieldname": "paid_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _(credit_or_debit_note),
				"fieldname": "return_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
				"hidden": 1,
			},
		]
		columns.append(
			{
				"label": _("Payment Due"),
				"fieldname": "payment_due",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
				"hidden": 1
			}
		)
		# Add dynamic columns for each range
		for idx, range_end in enumerate(self.ranges):
			range_start = 0 if idx == 0 else self.ranges[idx - 1]
			columns.append(
				{
					"label": _("({0}-{1} Days)").format(range_start, range_end),
					"fieldname": f"avg_outstanding_{idx + 1}",
					"fieldtype": "Currency",
					"options": "currency",
					"width": 150,
				}
			)
		for account in self.party_adjustment_accounts:
			columns.append(
				{
					"label": account,
					"fieldname": "adj_" + scrub(account),
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
					"is_adjustment": 1,
					"hidden": 1,
				}
			)
		columns += [
			{
				"label": _("Closing Balance"),
				"fieldname": "closing_balance",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldname": "currency",
				"fieldtype": "Link",
				"options": "Currency",
				"width": 50,
			},
		]
		if self.filters.party_type == "Customer":
			columns += [
				{
					"label": _("Territory"),
					"fieldname": "territory",
					"fieldtype": "Link",
					"options": "Territory",
					"hidden": 1,
				},
				{
					"label": _("Customer Group"),
					"fieldname": "customer_group",
					"fieldtype": "Link",
					"options": "Customer Group",
					"hidden": 1,
				},
				{
					"label": _("Cheque Received Count"),
					"fieldtype": "Int",
					"fieldname": "cheque_received_count",
					"width": 150,
				},
				{
					"label": _("Cheque Received Amount"),
					"fieldtype": "Currency",
					"fieldname": "cheque_received_amount",
					"width": 150,
				},
				{
					"label": _("Cheque Deposited Count"),
					"fieldtype": "Int",
					"fieldname": "cheque_deposited_count",
					"width": 150,
				},
				{
					"label": _("Cheque Deposited Amount"),
					"fieldtype": "Currency",
					"fieldname": "cheque_deposited_amount",
					"width": 150,
				},
			]
		else:
			columns += [
				{
					"label": _("Supplier Group"),
					"fieldname": "supplier_group",
					"fieldtype": "Link",
					"options": "Supplier Group",
					"hidden": 1,
				}
			]
		return columns

	def get_data(self):
		company_currency = frappe.get_cached_value("Company", self.filters.get("company"), "default_currency")
		invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
		reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"
		self.party_data = frappe._dict()
		for gle in self.gl_entries:
			party_details = self.party_details.get(gle.party)
			party_name = party_details.get(f"{scrub(self.filters.party_type)}_name", "")
			self.party_data.setdefault(
				gle.party,
				frappe._dict(
					{
						**party_details,
						"party_name": party_name,
						"opening_balance": 0,
						"invoiced_amount": 0,
						"paid_amount": 0,
						"return_amount": 0,
						"closing_balance": 0,
						"currency": company_currency,
						"payment_due": 0.0,
						"apple_id": "",
						**{f"avg_outstanding_{idx + 1}": self.avg_outstanding.get(gle.party, {}).get(idx, 0)
                           for idx in range(len(self.ranges))}
					}
				)
			)
			
			if self.filters.party_type == "Customer":
				apple_id_status = "Yes" if frappe.db.get_value("Customer", gle.party, "apple_id") else "No"
				self.party_data[gle.party]["apple_id"] = apple_id_status or ""
				
			amount = gle.get(invoice_dr_or_cr) - gle.get(reverse_dr_or_cr)
			self.party_data[gle.party].closing_balance += amount
			if gle.posting_date < self.filters.from_date or gle.is_opening == "Yes":
				self.party_data[gle.party].opening_balance += amount
			else:
				if amount > 0:
					self.party_data[gle.party].invoiced_amount += amount
				elif gle.voucher_no in self.return_invoices:
					self.party_data[gle.party].return_amount -= amount
				else:
					self.party_data[gle.party].paid_amount -= amount
		out = []
		for party, row in self.party_data.items():
			if (
				row.opening_balance
				or row.invoiced_amount
				or row.paid_amount
				or row.return_amount
				or row.closing_balance
				or any(row.get(f"avg_outstanding_{idx + 1}", 0) for idx in range(len(self.ranges)))
			):
				cheque_data = self.cheque_counts.get(party, {})
				row.cheque_received_count = cheque_data.get("cheque_received_count", 0)
				row.cheque_received_amount = cheque_data.get("cheque_received_amount", 0.0)
				row.cheque_deposited_count = cheque_data.get("cheque_deposited_count", 0)
				row.cheque_deposited_amount = cheque_data.get("cheque_deposited_amount", 0.0)
				total_party_adjustment = sum(
					amount for amount in self.party_adjustment_details.get(party, {}).values()
				)
				row.paid_amount -= total_party_adjustment
				adjustments = self.party_adjustment_details.get(party, {})
				for account in self.party_adjustment_accounts:
					row["adj_" + scrub(account)] = adjustments.get(account, 0)
				out.append(row)
		return out

	def get_gl_entries(self):
		gle = qb.DocType("GL Entry")
		query = (
			qb.from_(gle)
			.select(
				gle.posting_date,
				gle.party,
				gle.voucher_type,
				gle.voucher_no,
				gle.debit,
				gle.credit,
				gle.is_opening,
			)
			.where(
				(gle.docstatus < 2)
				& (gle.is_cancelled == 0)
				& (gle.party_type == self.filters.party_type)
				& (IfNull(gle.party, "") != "")
				& (gle.posting_date <= self.filters.to_date)
				& (gle.party.isin(self.parties))
			)
		)
		query = self.prepare_conditions(query)
		self.gl_entries = query.run(as_dict=True)

	def prepare_conditions(self, query):
		gle = qb.DocType("GL Entry")
		if self.filters.company:
			query = query.where(gle.company == self.filters.company)
		if self.filters.finance_book:
			query = query.where(IfNull(gle.finance_book, "") == self.filters.finance_book)
		if self.filters.cost_center:
			query = query.where((gle.cost_center).isin(self.filters.cost_center))
		if self.filters.project:
			query = query.where((gle.project).isin(self.filters.project))
		accounting_dimensions = get_accounting_dimensions(as_list=False)
		if accounting_dimensions:
			for dimension in accounting_dimensions:
				if self.filters.get(dimension.fieldname):
					if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
						self.filters[dimension.fieldname] = get_dimension_with_children(
							dimension.document_type, self.filters.get(dimension.fieldname)
						)
						query = query.where(
							(gle[dimension.fieldname]).isin(self.filters.get(dimension.fieldname))
						)
					else:
						query = query.where(
							(gle[dimension.fieldname]).isin(self.filters.get(dimension.fieldname))
						)
		return query

	def get_return_invoices(self):
		doctype = "Sales Invoice" if self.filters.party_type == "Customer" else "Purchase Invoice"
		filters = {
			"is_return": 1,
			"docstatus": 1,
			"posting_date": ["between", [self.filters.from_date, self.filters.to_date]],
			f"{scrub(self.filters.party_type)}": ["in", self.parties],
		}
		self.return_invoices = frappe.get_all(doctype, filters=filters, pluck="name")

	def get_party_adjustment_amounts(self):
		account_type = "Expense Account" if self.filters.party_type == "Customer" else "Income Account"
		invoice_dr_or_cr = "debit" if self.filters.party_type == "Customer" else "credit"
		reverse_dr_or_cr = "credit" if self.filters.party_type == "Customer" else "debit"
		round_off_account = frappe.get_cached_value("Company", self.filters.company, "round_off_account")
		current_period_vouchers = set()
		adjustment_voucher_entries = {}
		self.party_adjustment_details = {}
		self.party_adjustment_accounts = set()
		for gle in self.gl_entries:
			if (
				gle.is_opening != "Yes"
				and gle.posting_date >= self.filters.from_date
				and gle.posting_date <= self.filters.to_date
			):
				current_period_vouchers.add((gle.voucher_type, gle.voucher_no))
				adjustment_voucher_entries.setdefault((gle.voucher_type, gle.voucher_no), []).append(gle)
		if not current_period_vouchers:
			return
		gl = qb.DocType("GL Entry")
		query = (
			qb.from_(gl)
			.select(
				gl.posting_date, gl.account, gl.party, gl.voucher_type, gl.voucher_no, gl.debit, gl.credit
			)
			.where(
				(gl.docstatus < 2)
				& (gl.is_cancelled == 0)
				& (gl.posting_date.gte(self.filters.from_date))
				& (gl.posting_date.lte(self.filters.to_date))
				& (Tuple((gl.voucher_type, gl.voucher_no)).isin(current_period_vouchers))
				& (IfNull(gl.party, "") == "")
			)
		)
		query = self.prepare_conditions(query)
		gl_entries = query.run(as_dict=True)
		for gle in gl_entries:
			adjustment_voucher_entries[(gle.voucher_type, gle.voucher_no)].append(gle)
		for voucher_gl_entries in adjustment_voucher_entries.values():
			parties = {}
			accounts = {}
			has_irrelevant_entry = False
			for gle in voucher_gl_entries:
				if gle.account == round_off_account:
					continue
				elif gle.party:
					parties.setdefault(gle.party, 0)
					parties[gle.party] += gle.get(reverse_dr_or_cr) - gle.get(invoice_dr_or_cr)
				elif frappe.get_cached_value("Account", gle.account, "account_type") == account_type:
					accounts.setdefault(gle.account, 0)
					accounts[gle.account] += gle.get(invoice_dr_or_cr) - gle.get(reverse_dr_or_cr)
				else:
					has_irrelevant_entry = True
			if parties and accounts:
				if len(parties) == 1:
					party = next(iter(parties.keys()))
					for account, amount in accounts.items():
						self.party_adjustment_accounts.add(account)
						self.party_adjustment_details.setdefault(party, {})
						self.party_adjustment_details[party].setdefault(account, 0)
						self.party_adjustment_details[party][account] += amount
				elif len(accounts) == 1 and not has_irrelevant_entry:
					account = next(iter(accounts.keys()))
					self.party_adjustment_accounts.add(account)
					for party, amount in parties.items():
						self.party_adjustment_details.setdefault(party, {})
						self.party_adjustment_details[party].setdefault(account, 0)
						self.party_adjustment_details[party][account] += amount


def get_children(doctype, value):
	if not isinstance(value, list):
		value = [d.strip() for d in value.strip().split(",") if d]
	all_children = []
	for d in value:
		all_children += get_descendants_of(doctype, d)
		all_children.append(d)
	return list(set(all_children))


def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	return PartyLedgerSummaryReport(filters).run(args)