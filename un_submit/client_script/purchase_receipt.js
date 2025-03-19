frappe.ui.form.on("Purchase Receipt", {
    refresh: function(frm) {
        // Check if the current user has the "System Manager" role and docstatus is 1 (Submitted)
        if (frappe.user_roles.includes("System Manager") && frm.doc.docstatus === 1) {
            frm.add_custom_button('Switch to Draft', () => {
                frappe.warn(
                    __('Are you sure you want to revert this {0} to Draft?', [frm.doc.doctype]),
                    'This action will reset the document status.', // Description
                    () => { // Confirm Action
                        frappe.call({
                            method: 'un_submit.utils.revert_docstatus.revert_docstatus',  // Custom server-side method
                            args: {
                                doctype: frm.doc.doctype,
                                name: frm.doc.name
                            },
                            callback: function(response) {
                                if (!response.exc) {
                                    frappe.show_alert({
                                        message: __('Document has been successfully reverted to Draft.'),
                                        indicator: 'green'
                                    });
                                    frappe.ui.toolbar.clear_cache();
                                }
                            }
                        });
                    },
                    'Continue', // Rename confirmation button
                    true, // Show the cancel button
                );
            });
        }
    }
});
