# Path: your_app/your_app/dashboard_chart_source/monthly_sales_by_sales_rep/monthly_sales_by_sales_rep.py

import frappe

def get_chart_data(filters=None):
    conditions = ""
    values = {}

    if filters.get("month"):
        months = tuple(filters["month"])
        conditions += " AND DATE_FORMAT(si.posting_date, '%Y-%m') IN %(months)s"
        values["months"] = months

    data = frappe.db.sql("""
        SELECT 
            DATE_FORMAT(si.posting_date, '%Y-%m') AS month,
            sp.sales_person,
            SUM(si.base_net_total) AS total
        FROM `tabSales Invoice` si
        JOIN `tabSales Team` sp ON sp.parent = si.name
        WHERE si.docstatus = 1 {conditions}
        GROUP BY month, sp.sales_person
        ORDER BY month, sp.sales_person
    """.format(conditions=conditions), values=values, as_dict=True)

    dataset = {}
    labels = set()

    for row in data:
        labels.add(row["month"])
        if row["sales_person"] not in dataset:
            dataset[row["sales_person"]] = {}
        dataset[row["sales_person"]][row["month"]] = float(row["total"])

    labels = sorted(list(labels))
    datasets = []

    for sales_person, month_totals in dataset.items():
        row_data = [month_totals.get(label, 0) for label in labels]
        datasets.append({
            "name": sales_person,
            "values": row_data
        })

    return {
        "labels": labels,
        "datasets": datasets
    }
