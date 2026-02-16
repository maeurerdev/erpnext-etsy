from typing import Optional

import frappe
from frappe.model.document import Document
from frappe.utils import cstr

from etsy.datastruct import Listing, Property



class EtsyListing(Document):
	def get_attribute(self, property:Property, listing:Listing) -> Document:
		etsy_listing = self.name or str(listing.listing_id)
		if attribute_name := frappe.db.exists("Item Attribute", {"etsy_listing": etsy_listing, "etsy_property_id": str(property.property_id)}):
			attribute = frappe.get_doc("Item Attribute", attribute_name)
		else:
			attribute = frappe.new_doc("Item Attribute")
			attribute.attribute_name = f"{property.property_name}-{listing.listing_id}"
			attribute.etsy_listing = etsy_listing
			attribute.etsy_property_id = property.property_id
		return attribute
	
	def update_attributes(self, listing:Listing, item_template:Optional[Document]=None):
		for i, prop in enumerate(listing.inventory.products[0].property_values):
			attribute = self.get_attribute(prop, listing)
			for product in listing.inventory.products:
				property_value = product.property_values[i].values[0]
				if property_value in [x.attribute_value for x in attribute.item_attribute_values]: continue
				attribute.append(
					"item_attribute_values",
					{
						"attribute_value": property_value,
						"abbr": property_value[:28],
					},
				)
			attribute.save()

			if item_template is None: continue
			if attribute.name in [x.attribute for x in item_template.attributes]: continue
			item_template.append(
				"attributes",
				{
					"attribute": attribute.name,
				},
			)
	
	def update_items(self, listing:Listing):
		def get_item(item_code:str) -> Document:
			if item_name := frappe.db.exists("Item", {"item_code": item_code}):
				item = frappe.get_doc("Item", item_name)
			else:
				item = frappe.new_doc("Item")
				item.item_code = item_code
			
			item.etsy_listing = self.name
			return item

		if listing.has_variations:
            # create item template
			item_template = get_item(f"T{listing.listing_id}")
			item_template.has_variants = 1

			item_template.item_name = "["+ str(self.item_name or listing.title[:60]) +"]"
			item_template.item_group = self.item_group
			item_template.stock_uom = self.stock_uom
			item_template.is_stock_item = self.is_stock_item

			if len(listing.images) > 0:
				item_template.image = listing.images[0].get("url_170x135")
            
			self.update_attributes(listing, item_template)  # create & add variant attributes

			item_template.disabled = listing.state != "active"
			item_template.flags.ignore_mandatory = True
			item_template.save()

            # create item variant
			for product in listing.inventory.products:
				item = get_item(f"{product.product_id}")
				item.etsy_product_id = cstr(product.product_id)
				item.variant_of = item_template.name

				item.item_name = item_template.item_name[1:-1]
				item.item_group = item_template.item_group
				item.stock_uom = item_template.stock_uom
				item.is_stock_item = item_template.is_stock_item
				
				if len(listing.images) > 0:
					item.image = listing.images[0].get("url_170x135")

				description = ""
				name_extensions = []
				for prop in product.property_values:
					attribute_value = prop.values[0]
					description += f"<b>{prop.property_name}:</b> {attribute_value}<br>"

					attribute = self.get_attribute(prop, listing)
					for iav in attribute.item_attribute_values:
						if iav.attribute_value == attribute_value:
							name_extensions.append(iav.abbr if iav.abbr else attribute_value)
					
					if attribute.name in [x.attribute for x in item.attributes]: continue
					item.append(
						"attributes",
						{
							"attribute": attribute.name,
							"attribute_value": attribute_value,
						},
					)
				item.description = description
				item.item_name += "-" + "-".join(name_extensions)

				item.disabled = listing.state != "active" or product.is_deleted or product.offerings[0].is_deleted or not product.offerings[0].is_enabled
				item.flags.ignore_mandatory = True
				item.save()
        
		else:
			# create independent item (has no variants)
			product = listing.inventory.products[0]

			item = get_item(f"{product.product_id}")
			item.etsy_product_id = cstr(product.product_id)

			item.item_name = self.item_name or listing.title[:60]
			item.item_group = self.item_group
			item.stock_uom = self.stock_uom
			item.is_stock_item = self.is_stock_item
			
			if len(listing.images) > 0:
				item.image = listing.images[0].get("url_170x135")

			item.disabled = listing.state != "active" or product.is_deleted or product.offerings[0].is_deleted or not product.offerings[0].is_enabled
			item.flags.ignore_mandatory = True
			item.save()
