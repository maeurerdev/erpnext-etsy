import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    for key, value in frappe.get_hooks("etsy_custom_fields", {}).items():
        if isinstance(key, tuple):
            for doctype in key:
                create_custom_fields({doctype: value}, ignore_validate=True)
        else:
            create_custom_fields({key: value}, ignore_validate=True)

def before_uninstall():
    etsy_settings = frappe.get_single("Etsy Settings")
    if etsy_settings.item_scheduler_link:
        frappe.db.delete(
            "Scheduled Job Type",
            {"name": etsy_settings.item_scheduler_link}
        )
    if etsy_settings.sales_order_scheduler_link:
        frappe.db.delete(
            "Scheduled Job Type",
            {"name": etsy_settings.sales_order_scheduler_link}
        )

def after_uninstall():
    for key, value in frappe.get_hooks("etsy_custom_fields", {}).items():
        if isinstance(key, tuple):
            for doctype in key:
                delete_custom_fields(doctype, value)
        else:
            delete_custom_fields(key, value)


def delete_custom_fields(doctype, fields):
	frappe.db.delete(
		"Custom Field",
		{
			"fieldname": ("in", [field["fieldname"] for field in fields]),
			"dt": doctype,
		},
	)
	frappe.clear_cache(doctype=doctype)