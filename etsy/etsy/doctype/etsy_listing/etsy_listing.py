import re

import frappe
from frappe.model.document import Document
from frappe.utils import cstr

from etsy.datastruct import Listing, Property


class EtsyListing(Document):
	### hooks
	def before_save(self):
		for tag in self.tags:
			tag.quality, tag.comment = rate_tag(tag.tag)

			### public

	def get_attribute(self, property: Property, listing: Listing) -> Document:
		etsy_listing = self.name or str(listing.listing_id)
		if attribute_name := frappe.db.exists(
			"Item Attribute", {"etsy_listing": etsy_listing, "etsy_property_id": str(property.property_id)}
		):
			attribute = frappe.get_doc("Item Attribute", attribute_name)
		else:
			attribute = frappe.new_doc("Item Attribute")
			attribute.attribute_name = f"{property.property_name}-{listing.listing_id}"
			attribute.etsy_listing = etsy_listing
			attribute.etsy_property_id = property.property_id
		return attribute

	def update_attributes(self, listing: Listing, item_template: Document | None = None):
		for i, prop in enumerate(listing.inventory.products[0].property_values):
			attribute = self.get_attribute(prop, listing)
			for product in listing.inventory.products:
				property_value = product.property_values[i].values[0]
				if property_value in [x.attribute_value for x in attribute.item_attribute_values]:
					continue
				attribute.append(
					"item_attribute_values",
					{
						"attribute_value": property_value,
						"abbr": property_value[:28],
					},
				)
			attribute.save()

			if item_template is None:
				continue
			if attribute.name in [x.attribute for x in item_template.attributes]:
				continue
			item_template.append(
				"attributes",
				{
					"attribute": attribute.name,
				},
			)

	def update_items(self, listing: Listing):
		def get_item(item_code: str) -> Document:
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

			item_template.item_name = "[" + str(self.item_name or listing.title[:60]) + "]"
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

					if attribute.name in [x.attribute for x in item.attributes]:
						continue
					item.append(
						"attributes",
						{
							"attribute": attribute.name,
							"attribute_value": attribute_value,
						},
					)
				item.description = description
				item.item_name += "-" + "-".join(name_extensions)

				item.disabled = (
					listing.state != "active"
					or product.is_deleted
					or product.offerings[0].is_deleted
					or not product.offerings[0].is_enabled
				)
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

			item.disabled = (
				listing.state != "active"
				or product.is_deleted
				or product.offerings[0].is_deleted
				or not product.offerings[0].is_enabled
			)
			item.flags.ignore_mandatory = True
			item.save()


### Listing Utils
def rate_tag(tag: str) -> tuple[float, str]:
	"""
	Rates a single Etsy tag by length, word count, and formatting quality.

	Args:
	    tag: The tag string to evaluate.

	Returns:
	    A tuple of (rating, comment) where rating is a float between 0.0 and 1.0
	    and comment is a human-readable explanation of the score.
	"""
	if not tag or not tag.strip():
		return 0.0, "Tag is empty."

	tag = tag.strip()

	WEIGHTS = {
		"length": 0.40,
		"word_count": 0.35,
		"quality": 0.25,
	}

	issues = []  # formatting problems found
	positives = []  # things done well

	# ── 1. LENGTH SCORE ───────────────────────────────────────────────────────
	# Etsy allows a maximum of 20 characters per tag.
	# Tags closer to the limit tend to be more specific and SEO-relevant.
	ETSY_MAX = 20
	length = len(tag)

	if length == 0:
		length_score = 0.0
	elif length < 3:
		length_score = 0.05
		issues.append("tag is too short to be meaningful")
	elif length <= ETSY_MAX:
		# Linear scale starting at 5 characters
		length_score = min(1.0, (length - 2) / (ETSY_MAX - 2))
		if length >= 15:
			positives.append(f"good length ({length}/{ETSY_MAX} chars)")
	else:
		# Exceeds Etsy's limit — gets truncated, hard penalty
		length_score = max(0.0, 1.0 - (length - ETSY_MAX) * 0.25)
		issues.append(f"exceeds Etsy's {ETSY_MAX}-character limit ({length} chars)")

	# ── 2. WORD COUNT SCORE ───────────────────────────────────────────────────
	# Long-tail phrases (2–4 words) are the sweet spot for Etsy SEO.
	# Single-word tags are too generic; 5+ words tend to be overstuffed.
	words = [w for w in tag.split() if w]
	word_count = len(words)

	word_score_map = {
		0: 0.0,
		1: 0.15,
		2: 0.75,
		3: 1.00,
		4: 0.90,
		5: 0.65,
	}
	if word_count in word_score_map:
		word_score = word_score_map[word_count]
	else:
		# 6+ words: diminishing returns
		word_score = max(0.2, 0.65 - (word_count - 5) * 0.1)

	if word_count == 1:
		issues.append("single-word tags are too generic")
	elif word_count == 2:
		positives.append("two-word phrase, decent specificity")
	elif word_count == 3:
		positives.append("three-word phrase, optimal for Etsy SEO")
	elif word_count == 4:
		positives.append("four-word phrase, good long-tail coverage")
	elif word_count >= 5:
		issues.append(f"phrase may be too long ({word_count} words)")

	# ── 3. QUALITY SCORE ─────────────────────────────────────────────────────
	# Checks for formatting issues that reduce discoverability or violate
	# Etsy's tag guidelines (special characters, ALL CAPS, underscores, etc.)
	quality_score = 1.0
	deductions = []

	# Tag consists of digits only — meaningless as a search term
	if re.fullmatch(r"[\d\s]+", tag):
		deductions.append(0.80)
		issues.append("tag contains only numbers")

	# Special characters (hyphens and common accented letters are allowed)
	special_chars = re.findall(r"[^\w\s\-äöüÄÖÜßàáâãèéêëìíîïòóôõùúûñç]", tag)
	if special_chars:
		penalty = min(0.50, len(special_chars) * 0.15)
		deductions.append(penalty)
		issues.append(f"contains special character(s): {''.join(set(special_chars))}")

	# Underscores instead of spaces hurt readability and search matching
	if "_" in tag:
		deductions.append(0.20)
		issues.append("use spaces instead of underscores")

	# ALL CAPS looks spammy and hurts user experience
	if len(tag) > 3 and tag.isupper():
		deductions.append(0.25)
		issues.append("avoid writing tags in ALL CAPS")

	# Single word AND very short — doubly weak
	if word_count == 1 and length <= 4:
		deductions.append(0.20)

	quality_score = max(0.0, quality_score - sum(deductions))

	if not issues and quality_score == 1.0:
		positives.append("no formatting issues detected")

	# ── FINAL RATING ──────────────────────────────────────────────────────────
	final = (
		WEIGHTS["length"] * length_score
		+ WEIGHTS["word_count"] * word_score
		+ WEIGHTS["quality"] * quality_score
	)
	rating = round(min(1.0, max(0.0, final)), 4)

	# ── BUILD COMMENT ─────────────────────────────────────────────────────────
	lines = []
	for positive in positives:
		lines.append(f"✅ {positive}")
	for issue in issues:
		lines.append(f"⚠️ {issue}")

	comment = "\n".join(lines) if lines else "+ tag looks good"

	return rating, comment
