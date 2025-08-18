frappe.ui.form.on('Invoice Email Review', {
  refresh(frm) {
    if (frm.doc.docstatus === 0 && frm.doc.status === "Draft") {
      frm.add_custom_button('Send Now', () => {
        if (!frm.doc.customer_email) {
          frappe.msgprint("Customer Email is missing.");
          return;
        }
        frappe.confirm(
          `Send invoice email to <b>${frappe.utils.escape_html(frm.doc.customer_email)}</b> now?`,
          () => {
            frappe.call({
              method: "custom_billing.utils.email_outbox.send_invoice_email",
              args: { review_name: frm.doc.name },
              freeze: true,
              callback: () => {
                frappe.msgprint("Email sent (or attempted). Refresh to see status.");
                frm.reload_doc();
              }
            });
          }
        );
      }).addClass("btn-primary");
    }
  }
});
