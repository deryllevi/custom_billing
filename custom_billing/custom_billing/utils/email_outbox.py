import frappe
from frappe.utils import get_first_day, get_last_day, nowdate
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def populate_invoice_email_review():
    """
    Create one 'Invoice Email Review' draft per submitted Sales Invoice due this month.
    - No emails sent here.
    - Marks 'Skipped' if customer email is missing.
    - Attaches a preview PDF (best-effort).
    - Idempotent: won't duplicate entries for the same invoice.
    """
    today = nowdate()
    month_start = get_first_day(today)
    month_end = get_last_day(today)

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,  # submitted
            "due_date": ["between", [month_start, month_end]],
        },
        fields=["name", "customer_name", "contact_email"]
    )

    for inv in invoices:
        if frappe.db.exists("Invoice Email Review", {"sales_invoice": inv["name"]}):
            continue

        has_email = bool(inv.get("contact_email"))
        status = "Draft" if has_email else "Skipped"
        subject = f"Invoice {inv['name']}"
        message = (
            f"Dear {inv.get('customer_name') or 'Customer'},<br><br>"
            f"Please find attached your invoice <b>{inv['name']}</b>.<br><br>"
            f"Thank you."
        )

        doc = frappe.get_doc({
            "doctype": "Invoice Email Review",
            "sales_invoice": inv["name"],
            "customer_name": inv.get("customer_name"),
            "customer_email": inv.get("contact_email") or "",
            "email_subject": subject,
            "email_message": message,
            "status": status
        }).insert(ignore_permissions=True)

        # Optional: attach a preview PDF to the review record
        try:
            pdf = frappe.get_print(
                doctype="Sales Invoice",
                name=inv["name"],
                print_format=None,  # Standard
                as_pdf=True
            )
            save_file(
                fname=f"{inv['name']}.pdf",
                content=pdf,
                dt="Invoice Email Review",
                dn=doc.name,
                is_private=1
            )
        except Exception:
            pass

    frappe.db.commit()


@frappe.whitelist()
def send_invoice_email(review_name: str):
    """
    Finance Officer clicks 'Send Now' -> send immediately to the customer's email.
    - Regenerates a fresh PDF from the Sales Invoice.
    - Updates status to Sent on success, Error on failure.
    """
    if not frappe.has_permission("Invoice Email Review", "write"):
        frappe.throw("Not permitted.")

    doc = frappe.get_doc("Invoice Email Review", review_name)

    if doc.status != "Draft":
        frappe.throw("Only Draft items can be sent.")

    if not doc.customer_email:
        doc.status = "Error"
        doc.error_message = "Customer email is missing."
        doc.save(ignore_permissions=True)
        return

    try:
        inv = frappe.get_doc("Sales Invoice", doc.sales_invoice)

        pdf_data = frappe.get_print(
            doctype="Sales Invoice",
            name=inv.name,
            print_format=None,  # use Standard or set your site default
            as_pdf=True
        )

        frappe.sendmail(
            recipients=[doc.customer_email],
            subject=doc.email_subject or f"Invoice {inv.name}",
            message=doc.email_message or "",
            attachments=[{"fname": f"{inv.name}.pdf", "fcontent": pdf_data}],
        )

        doc.status = "Sent"
        doc.error_message = ""
        doc.save(ignore_permissions=True)

    except Exception:
        doc.status = "Error"
        doc.error_message = frappe.get_traceback()
        doc.save(ignore_permissions=True)
        frappe.log_error(message=frappe.get_traceback(), title="Invoice Email Send Error")
        raise
