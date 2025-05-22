"""
custom_fields = {
    "Doctype": [
        {
            "property_1": "value",
            ...:...;
        }
    ]
}
"""

config = {
    "Purchase Invoice": [
            {
               "fieldname": "ignore_linked_document",
                "label": "Ignore Linked Document",
                "fieldtype": "Check",
                "insert_after": "due_date",
                "hidden": 1,
                
            },
    ]
}