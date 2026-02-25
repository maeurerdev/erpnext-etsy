try:
	from frappe.tests import UnitTestCase as FrappeTestCase  # Frappe v16+
except ImportError:
	from frappe.tests.utils import FrappeTestCase  # Frappe v15


class TestEtsyListing(FrappeTestCase):
	pass
