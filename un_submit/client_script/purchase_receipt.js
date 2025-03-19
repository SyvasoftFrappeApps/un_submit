frappe.ui.form.on("Purchase Receipt", {
    refresh: function(frm) {
        let is_submitted = frm.doc.docstatus === 1;
        let button_label = is_submitted ? "Switch to Draft" : "Switch to Submit";
        let confirmation_message = is_submitted
            ? __("Are you sure you want to revert this {0} to Draft?", [frm.doc.doctype])
            : __("Are you sure you want to submit this {0}?", [frm.doc.doctype]);

        frm.add_custom_button(button_label, () => {
            frappe.warn(
                confirmation_message,
                "This action will change the document status.", // Description
                () => {
                    toggle_docstatus(frm);
                },
                "Continue", // Confirm button label
                true // Show cancel button
            );
        });
    }
});

function toggle_docstatus(frm) {
    frappe.call({
        method: "un_submit.utils.revert_docstatus.revert_docstatus",
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
