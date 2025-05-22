frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(
                frm.doc.ignore_linked_document ? "Disable Ignore Linked" : "Enable Ignore Linked",
                () => {
                    frappe.call({
                        method: "un_submit.utils.revert_docstatus.toggle_ignore_link_sql",
                        args: {
                            doctype: frm.doc.doctype,
                            docname: frm.doc.name
                        },
                        callback(r) {
                            if (!r.exc) {
                                frappe.msgprint(`Ignore Linked is now: ${r.message.new_value ? "Enabled" : "Disabled"}`);
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }
    }
});
