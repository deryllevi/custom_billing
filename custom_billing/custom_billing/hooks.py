from . import __version__ as app_version

app_name = "custom_billing"
app_title = "Custom Billing"
app_publisher = "Your Name / Company"
app_description = "Finance-officer reviewed invoice emailing for ERPNext v14"
app_email = "you@example.com"
app_license = "MIT"

# Run the populate job on the 1st of every month
scheduler_events = {
    "monthly": [
        "custom_billing.utils.email_outbox.populate_invoice_email_review"
    ]
}

# No fixtures by default
fixtures = []
