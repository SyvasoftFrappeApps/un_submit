frappe.ui.form.on("Purchase Receipt", {
    refresh: function(frm) {
        // When the document is submitted, show "Switch to Draft"
        if (frm.doc.docstatus === 1) {
            let button_label = "Switch to Draft";
            let confirmation_message = __("Are you sure you want to revert this {0} to Draft?", [frm.doc.doctype]);
            
            frm.add_custom_button(button_label, () => {
                frappe.warn(
                    confirmation_message,
                    "This action will change the document status.",
                    () => {
                        // Call revert_docstatus for "Switch to Draft"
                        frappe.call({
                            method: "un_submit.utils.revert_docstatus.revert_docstatus",
                            args: {
                                doctype: frm.doc.doctype,
                                name: frm.doc.name
                            },
                            callback: function(response) {
                                if (!response.exc) {
                                    frappe.show_alert({
                                        message: __("Document has been successfully updated (reverted to Draft)."),
                                        indicator: "green"
                                    });
                                    frappe.ui.toolbar.clear_cache();
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    "Continue",
                    true
                );
            });
        }
        // When document is draft and ignore_permissions is enabled, show "Switch to Submit"
        else if (frm.doc.docstatus === 0 && frm.doc.ignore_permissions === 1) {
            let button_label = "Switch to Submit";
            let confirmation_message = __("Are you sure you want to submit this {0}?", [frm.doc.doctype]);
            
            frm.add_custom_button(button_label, () => {
                frappe.warn(
                    confirmation_message,
                    "This action will change the document status.",
                    () => {
                        // First, call revert_docstatus (common for both actions)
                        frappe.call({
                            method: "un_submit.utils.revert_docstatus.revert_docstatus",
                            args: {
                                doctype: frm.doc.doctype,
                                name: frm.doc.name
                            },
                            callback: function(response) {
                                if (!response.exc) {
                                    // Then, call after_submit_purchase_receipt with a plain JS object and method flag
                                    frappe.call({
                                        method: "un_submit.server_script.purchase_receipt_override.after_submit_purchase_receipt",
                                        args: {
                                            doc: JSON.parse(JSON.stringify(frm.doc)),
                                            method: "submit"
                                        },
                                        callback: function(response2) {
                                            if (!response2.exc) {
                                                frappe.show_alert({
                                                    message: __("Document has been successfully submitted."),
                                                    indicator: "green"
                                                });
                                                frappe.ui.toolbar.clear_cache();
                                                frm.reload_doc();
                                            }
                                        }
                                    });
                                }
                            }
                        });
                    },
                    "Continue",
                    true
                );
            });
        }
    }
});
