import frappe

try:
	from frappe.tests import UnitTestCase as FrappeTestCase  # Frappe v16+
except ImportError:
	from frappe.tests.utils import FrappeTestCase  # Frappe v15

from etsy.etsy.doctype.etsy_shop.etsy_shop import (
	short_title,
)


class TestShortTitle(FrappeTestCase):
	"""Tests for the short_title utility function."""

	def test_simple_title(self):
		self.assertEqual(short_title("Simple Title"), "Simple Title")

	def test_comma_split(self):
		self.assertEqual(short_title("Part One, Part Two, Part Three"), "Part One")

	def test_semicolon_split(self):
		self.assertEqual(short_title("Part One; Part Two"), "Part One")

	def test_pipe_split(self):
		self.assertEqual(short_title("Part One | Part Two"), "Part One")

	def test_bullet_split(self):
		result = short_title("Part One \u2022 Part Two")
		self.assertEqual(result, "Part One")

	def test_dash_split(self):
		self.assertEqual(short_title("Part One - Part Two"), "Part One")

	def test_endash_split(self):
		result = short_title("Part One \u2013 Part Two")
		self.assertEqual(result, "Part One")

	def test_html_entity_replacement(self):
		self.assertEqual(short_title("He said &quot;hello&quot;"), 'He said "hello"')

	def test_truncation_to_60_chars(self):
		long_title = "A" * 100
		self.assertEqual(len(short_title(long_title)), 60)

	def test_strips_whitespace(self):
		self.assertEqual(short_title("  Hello World  , more stuff"), "Hello World")
