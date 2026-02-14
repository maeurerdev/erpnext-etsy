# Copyright (c) 2026, Cornstarch3D and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from etsy.etsy.doctype.etsy_settings.etsy_settings import (
	RECEIPTS_SCHEDULED_JOB_TYPE_METHOD,
	LISTINGS_SCHEDULED_JOB_TYPE_METHOD,
)


class TestEtsySettings(FrappeTestCase):
	def setUp(self):
		self.settings = frappe.get_single("Etsy Settings")
		self.settings.etsy_enabled = 0
		self.settings.sales_order_sync_interval = 5
		self.settings.item_sync_interval = 24
		self.settings.save()

	def tearDown(self):
		for field in ("sales_order_scheduler_link", "item_scheduler_link"):
			link = self.settings.get(field)
			if link and frappe.db.exists("Scheduled Job Type", link):
				frappe.delete_doc("Scheduled Job Type", link, force=True)
		self.settings.reload()
		self.settings.sales_order_scheduler_link = None
		self.settings.item_scheduler_link = None
		self.settings.db_update()
		frappe.db.commit()

	def test_save_creates_scheduled_jobs(self):
		"""Saving with etsy_enabled creates Scheduled Job Type entries."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 10
		self.settings.item_sync_interval = 6
		self.settings.save()

		self.assertIsNotNone(self.settings.sales_order_scheduler_link)
		self.assertIsNotNone(self.settings.item_scheduler_link)

		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.method, RECEIPTS_SCHEDULED_JOB_TYPE_METHOD)
		self.assertEqual(so_job.frequency, "Cron")
		self.assertEqual(so_job.cron_format, "*/10 * * * *")
		self.assertEqual(so_job.stopped, 0)

		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.method, LISTINGS_SCHEDULED_JOB_TYPE_METHOD)
		self.assertEqual(item_job.frequency, "Cron")
		self.assertEqual(item_job.cron_format, "0 */6 * * *")
		self.assertEqual(item_job.stopped, 0)

	def test_disabled_stops_scheduled_jobs(self):
		"""When etsy_enabled is 0, scheduled jobs should be stopped."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 5
		self.settings.item_sync_interval = 12
		self.settings.save()

		self.settings.etsy_enabled = 0
		self.settings.save()

		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.stopped, 1)

		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.stopped, 1)

	def test_zero_interval_stops_job(self):
		"""Setting interval to 0 stops the job even when enabled."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 0
		self.settings.item_sync_interval = 0
		self.settings.save()

		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.stopped, 1)
		self.assertEqual(so_job.cron_format, "*/1 * * * *")

		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.stopped, 1)
		self.assertEqual(item_job.cron_format, "0 */1 * * *")

	def test_sales_order_interval_clamped_to_60(self):
		"""sales_order_sync_interval is clamped to a maximum of 60."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 120
		self.settings.save()

		self.assertEqual(self.settings.sales_order_sync_interval, 60)
		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.cron_format, "*/60 * * * *")

	def test_item_interval_clamped_to_24(self):
		"""item_sync_interval is clamped to a maximum of 24."""
		self.settings.etsy_enabled = 1
		self.settings.item_sync_interval = 100
		self.settings.save()

		self.assertEqual(self.settings.item_sync_interval, 24)
		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.cron_format, "0 */24 * * *")

	def test_negative_interval_clamped_to_zero(self):
		"""Negative intervals are clamped to 0."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = -5
		self.settings.item_sync_interval = -10
		self.settings.save()

		self.assertEqual(self.settings.sales_order_sync_interval, 0)
		self.assertEqual(self.settings.item_sync_interval, 0)

	def test_reuses_existing_scheduled_job(self):
		"""Saving twice reuses the same Scheduled Job Type document."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 5
		self.settings.save()

		first_so_link = self.settings.sales_order_scheduler_link
		first_item_link = self.settings.item_scheduler_link

		self.settings.sales_order_sync_interval = 10
		self.settings.save()

		self.assertEqual(self.settings.sales_order_scheduler_link, first_so_link)
		self.assertEqual(self.settings.item_scheduler_link, first_item_link)

	def test_get_scheduler_returns_new_doc_for_invalid_link(self):
		"""get_scheduler returns a new unsaved doc if the link is invalid."""
		job = self.settings.get_scheduler("nonexistent-job-12345")
		self.assertTrue(job.is_new())

	def test_get_scheduler_returns_new_doc_for_none(self):
		"""get_scheduler returns a new unsaved doc if the link is None."""
		job = self.settings.get_scheduler(None)
		self.assertTrue(job.is_new())

	def test_receipts_cron_format(self):
		"""Receipts scheduler uses minute-based cron format."""
		self.settings.etsy_enabled = 1
		self.settings.sales_order_sync_interval = 15
		self.settings.save()

		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.cron_format, "*/15 * * * *")

	def test_listings_cron_format(self):
		"""Listings scheduler uses hour-based cron format."""
		self.settings.etsy_enabled = 1
		self.settings.item_sync_interval = 8
		self.settings.save()

		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.cron_format, "0 */8 * * *")

	def test_scheduled_job_methods(self):
		"""Scheduled jobs reference the correct API methods."""
		self.settings.etsy_enabled = 1
		self.settings.save()

		so_job = frappe.get_doc("Scheduled Job Type", self.settings.sales_order_scheduler_link)
		self.assertEqual(so_job.method, "etsy.api.synchronise_receipts")

		item_job = frappe.get_doc("Scheduled Job Type", self.settings.item_scheduler_link)
		self.assertEqual(item_job.method, "etsy.api.synchronise_listings")
