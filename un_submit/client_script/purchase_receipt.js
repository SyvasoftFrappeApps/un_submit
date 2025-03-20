frappe.ui.form.on("Purchase Receipt", {
    refresh: function(frm) {
        let is_submitted = frm.doc.docstatus === 1;

        // Always show the "Switch to Draft" button if the document is submitted
        if (is_submitted) {
            let button_label = "Switch to Draft";
            let confirmation_message = __("Are you sure you want to revert this {0} to Draft?", [frm.doc.doctype]);
            
            frm.add_custom_button(button_label, () => {
                frappe.warn(
                    confirmation_message,
                    "This action will change the document status.",
                    () => {
                        toggle_docstatus(frm, "draft");
                    },
                    "Continue",
                    true
                );
            });
        } else {
            // Only show "Switch to Submit" if ignore_permissions is enabled
            if (frm.doc.ignore_permissions === 1) {
                let button_label = "Switch to Submit";
                let confirmation_message = __("Are you sure you want to submit this {0}?", [frm.doc.doctype]);
                
                frm.add_custom_button(button_label, () => {
                    frappe.warn(
                        confirmation_message,
                        "This action will change the document status.",
                        () => {
                            toggle_docstatus(frm, "submit");
                        },
                        "Continue",
                        true
                    );
                });
            }
        }
    }
});

function toggle_docstatus(frm, action) {
    // Set the method based on the action required
    let method = action === "draft" 
        ? "un_submit.utils.revert_docstatus.revert_docstatus" 
        : "un_submit.server_script.purchase_receipt_override.after_submit_purchase_receipt";

    frappe.call({
        method: method,
        args: {
            doctype: frm.doc.doctype,
            name: frm.doc.name
        },
        callback: function(response) {
            if (!response.exc) {
                frappe.show_alert({
                    message: __("Document has been successfully updated."),
                    indicator: "green"
                });
                frappe.ui.toolbar.clear_cache();
                frm.reload_doc();
            }
        }
    });
}
