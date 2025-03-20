frappe.ui.form.on("Purchase Receipt", {
    refresh: function(frm) {
        // Hide/Show Submit button based on conditions
        if (frm.doc.docstatus === 0 && frm.doc.ignore_permissions === 1) {
            frm.page.btn_primary.hide();
        } 

        // When the document is submitted, show "Switch to Draft"
        if (frm.doc.docstatus === 1) {
            let button_label = "Switch to Draft";
            let confirmation_message = __("Are you sure you want to revert this {0} to Draft?", [frm.doc.doctype]);

            frm.add_custom_button(button_label, () => {
                
                // Save the form after successful submission
                frm.save_or_update();
                frappe.warn(
                    confirmation_message,
                    "This action will change the document status.",
                    () => {
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
                
                // Save the form after successful submission
                frm.save_or_update();
                frappe.warn(
                    confirmation_message,
                    "This action will change the document status.",
                    () => {
                        frappe.call({
                            method: "un_submit.utils.revert_docstatus.revert_docstatus",
                            args: {
                                doctype: frm.doc.doctype,
                                name: frm.doc.name
                            },
                            callback: function(response) {
                                if (!response.exc) {
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
