# Copyright (c) 2026, Cornstarch3D and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document



RECEIPTS_SCHEDULED_JOB_TYPE_METHOD = "etsy.api.synchronise_receipts"
LISTINGS_SCHEDULED_JOB_TYPE_METHOD = "etsy.api.synchronise_listings"


class EtsySettings(Document):
	@property
	def sales_order_last_sync(self):
		return self.get_scheduler(self.sales_order_scheduler_link).last_execution
	
	@property
	def sales_order_next_sync(self):
		return self.get_scheduler(self.sales_order_scheduler_link).next_execution
	
	@property
	def item_last_sync(self):
		return self.get_scheduler(self.item_scheduler_link).last_execution
	
	@property
	def item_next_sync(self):
		return self.get_scheduler(self.item_scheduler_link).next_execution
	
	def before_save(self):
		### receipts
		sales_order_interval = min(max(0, self.sales_order_sync_interval), 60)
		self.sales_order_sync_interval = sales_order_interval

		sales_order_job = self.get_scheduler(self.sales_order_scheduler_link)
		sales_order_job.method = RECEIPTS_SCHEDULED_JOB_TYPE_METHOD
		sales_order_job.frequency = "Cron"
		sales_order_job.cron_format = f"*/{max(1, sales_order_interval)} * * * *"  # runs every X minutes
		sales_order_job.stopped = 1 - (self.etsy_enabled * min(1, sales_order_interval))
		sales_order_job.save()

		self.sales_order_scheduler_link = sales_order_job.name

		### listings
		item_interval = min(max(0, self.item_sync_interval), 24)
		self.item_sync_interval = item_interval

		item_job = self.get_scheduler(self.item_scheduler_link)
		item_job.method = LISTINGS_SCHEDULED_JOB_TYPE_METHOD
		item_job.frequency = "Cron"
		item_job.cron_format = f"0 */{max(1, item_interval)} * * *"  # runs every X hours
		item_job.stopped = 1 - (self.etsy_enabled * min(1, item_interval))
		item_job.save()

		self.item_scheduler_link = item_job.name


	def get_scheduler(self, scheduler_link):
		"Return `Scheduled Job Type` if it exists, else create a new one"
		if scheduler_link and frappe.db.exists("Scheduled Job Type", scheduler_link):
			return frappe.get_doc("Scheduled Job Type", scheduler_link)
		else:
			return frappe.new_doc("Scheduled Job Type")
