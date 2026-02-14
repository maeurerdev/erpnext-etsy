# Copyright (c) 2026, Cornstarch3D and Contributors
# See license.txt

from unittest.mock import patch, MagicMock

import frappe
from frappe.tests.utils import FrappeTestCase

from etsy.etsy.doctype.etsy_shop.etsy_shop import (
	EtsyShop,
	LISTING_STATES,
	short_title,
	callback,
	has_token,
)
from etsy.datastruct import Me


def get_test_company():
	"""Return the first available Company or create one for tests."""
	company = frappe.db.get_value("Company", filters={}, fieldname="name")
	if not company:
		company_doc = frappe.get_doc({
			"doctype": "Company",
			"company_name": "_Test Etsy Company",
			"abbr": "_TEC",
			"default_currency": "EUR",
			"country": "Germany",
		}).insert(ignore_if_duplicate=True)
		company = company_doc.name
	return company


def get_test_account(company):
	"""Return a test account for the given company."""
	account = frappe.db.get_value("Account", {"company": company, "account_type": "Bank"})
	if not account:
		account = frappe.db.get_value("Account", {"company": company})
	return account


def create_etsy_shop(shop_name=None, **kwargs):
	"""Create an Etsy Shop document for testing."""
	company = get_test_company()
	account = get_test_account(company)

	doc = frappe.get_doc({
		"doctype": "Etsy Shop",
		"shop_name": shop_name or frappe.generate_hash(length=10),
		"company": company,
		"sales_tax_account": account,
		"shipping_tax_account": account,
		"bank_account_physical": account,
		"bank_account_digital": account,
		**kwargs,
	})
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_if_duplicate=True)
	return doc


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
		self.assertEqual(short_title('He said &quot;hello&quot;'), 'He said "hello"')

	def test_truncation_to_60_chars(self):
		long_title = "A" * 100
		self.assertEqual(len(short_title(long_title)), 60)

	def test_strips_whitespace(self):
		self.assertEqual(short_title("  Hello World  , more stuff"), "Hello World")


class TestEtsyShop(FrappeTestCase):
	def setUp(self):
		self.shop = create_etsy_shop()

	def tearDown(self):
		frappe.delete_doc("Etsy Shop", self.shop.name, force=True)
		frappe.db.commit()

	def test_creation(self):
		"""Etsy Shop can be created with required fields."""
		self.assertTrue(frappe.db.exists("Etsy Shop", self.shop.name))
		self.assertEqual(self.shop.status, "Disconnected")

	def test_shop_name_is_unique(self):
		"""Duplicate shop_name raises an error."""
		self.assertRaises(
			frappe.DuplicateEntryError,
			create_etsy_shop,
			shop_name=self.shop.shop_name,
		)

	def test_validate_sets_redirect_uri(self):
		"""validate() constructs the redirect_uri from the base URL."""
		self.shop.use_localhost = 0
		self.shop.save()

		base_url = frappe.utils.get_url()
		expected_path = f"/api/method/etsy.etsy.doctype.etsy_shop.etsy_shop.callback/{self.shop.name}"
		self.assertIn(expected_path, self.shop.redirect_uri)
		self.assertTrue(self.shop.redirect_uri.startswith(base_url.split(":")[0]))

	def test_validate_localhost_redirect_uri(self):
		"""When use_localhost is set, redirect_uri uses localhost."""
		self.shop.use_localhost = 1
		self.shop.save()

		self.assertIn("localhost", self.shop.redirect_uri)

	def test_disconnect_clears_tokens(self):
		"""disconnect_etsy_shop clears all connection fields."""
		self.shop.user_id = "12345"
		self.shop.shop_id = "67890"
		self.shop.token_type = "Bearer"
		self.shop.token_state = "some-state"
		self.shop.status = "Connected"
		self.shop.save()

		self.shop.disconnect_etsy_shop()
		self.shop.reload()

		self.assertFalse(self.shop.user_id)
		self.assertFalse(self.shop.shop_id)
		self.assertFalse(self.shop.token_type)
		self.assertFalse(self.shop.token_state)
		self.assertEqual(self.shop.expires_in, 0)
		self.assertEqual(self.shop.status, "Disconnected")

	def test_token_exists_without_token(self):
		"""token_exists returns False when no access_token is set."""
		self.assertFalse(self.shop.token_exists())

	def test_get_auth_header_without_token(self):
		"""get_auth_header returns None when no access_token exists."""
		result = self.shop.get_auth_header()
		self.assertIsNone(result)

	def test_generate_code_verifier(self):
		"""generate_code_verifier creates a URL-safe string and saves it."""
		verifier = self.shop.generate_code_verifier()
		self.assertIsInstance(verifier, str)
		self.assertTrue(len(verifier) > 0)
		self.assertEqual(self.shop.code_verifier, verifier)

	def test_generate_code_challenge(self):
		"""generate_code_challenge creates a base64url-encoded SHA256 hash."""
		self.shop.generate_code_verifier()
		challenge = self.shop.generate_code_challenge()

		self.assertIsInstance(challenge, str)
		self.assertTrue(len(challenge) > 0)
		# Should not contain padding characters
		self.assertNotIn("=", challenge)

	def test_code_challenge_deterministic(self):
		"""Same code_verifier produces the same code_challenge."""
		self.shop.generate_code_verifier()
		challenge1 = self.shop.generate_code_challenge()
		challenge2 = self.shop.generate_code_challenge()
		self.assertEqual(challenge1, challenge2)

	def test_initiate_web_application_flow_requires_client_id(self):
		"""initiate_web_application_flow throws if client_id is missing."""
		self.shop.client_id = None
		self.shop.client_secret = "test-secret"
		self.shop.save()

		self.assertRaises(frappe.ValidationError, self.shop.initiate_web_application_flow)

	def test_initiate_web_application_flow_requires_client_secret(self):
		"""initiate_web_application_flow throws if client_secret is missing."""
		self.shop.client_id = "test-client-id"
		self.shop.client_secret = None
		self.shop.save()

		self.assertRaises(frappe.ValidationError, self.shop.initiate_web_application_flow)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyShop.get_oauth2_session")
	def test_initiate_web_application_flow_returns_url(self, mock_session):
		"""initiate_web_application_flow returns an authorization URL."""
		mock_oauth = MagicMock()
		mock_oauth.authorization_url.return_value = ("https://www.etsy.com/oauth/connect?test=1", "test-state")
		mock_session.return_value = mock_oauth

		self.shop.client_id = "test-client-id"
		self.shop.client_secret = "test-secret"
		self.shop.save()

		url = self.shop.initiate_web_application_flow()
		self.assertIn("etsy.com", url)
		self.assertEqual(self.shop.token_state, "test-state")

	def test_token_json_structure(self):
		"""token_json returns dict with expected keys."""
		result = self.shop.token_json()
		self.assertIn("access_token", result)
		self.assertIn("refresh_token", result)
		self.assertIn("expires_in", result)
		self.assertIn("token_type", result)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyAPI")
	def test_token_update_connected(self, mock_api_class):
		"""token_update sets status to Connected when getMe succeeds."""
		mock_api = MagicMock()
		mock_api.getMe.return_value = Me(user_id=111, shop_id=222)
		mock_api_class.return_value = mock_api

		token_data = {
			"access_token": "test-access-token",
			"refresh_token": "test-refresh-token",
			"token_type": "Bearer",
			"expires_in": 3600,
		}
		self.shop.token_update(token_data)
		self.shop.reload()

		self.assertEqual(self.shop.status, "Connected")
		self.assertEqual(self.shop.user_id, "111")
		self.assertEqual(self.shop.shop_id, "222")
		self.assertEqual(self.shop.token_type, "Bearer")
		self.assertEqual(self.shop.expires_in, 3600)
		self.assertIsNone(self.shop.token_state)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyAPI")
	def test_token_update_disconnected_on_failure(self, mock_api_class):
		"""token_update sets status to Disconnected when getMe fails."""
		mock_api_class.side_effect = Exception("API Error")

		token_data = {
			"access_token": "test-access-token",
			"refresh_token": "test-refresh-token",
			"token_type": "Bearer",
			"expires_in": 3600,
		}
		self.shop.token_update(token_data)
		self.shop.reload()

		self.assertEqual(self.shop.status, "Disconnected")

	def test_update_expires_in(self):
		"""update_expires_in sets both expires_in and expires_in_datetime."""
		self.shop.update_expires_in(7200)
		self.assertEqual(self.shop.expires_in, 7200)
		self.assertIsNotNone(self.shop.expires_in_datetime)

	def test_import_listings_invalid_state(self):
		"""import_listings raises on invalid listing_state."""
		self.assertRaises(
			frappe.ValidationError,
			self.shop.import_listings,
			listing_state="invalid_state",
		)

	def test_import_listings_valid_states(self):
		"""All defined LISTING_STATES should be accepted (no exception on empty API)."""
		for state in LISTING_STATES:
			with patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyAPI") as mock_api_class:
				mock_api = MagicMock()
				mock_api.getListingsByShop.return_value = (0, [])
				mock_api_class.return_value = mock_api
				# Should not raise
				self.shop.import_listings(listing_state=state, etsy_api=mock_api)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyAPI")
	def test_import_listings_all_iterates_states(self, mock_api_class):
		"""import_listings with 'all' calls itself for each LISTING_STATE."""
		mock_api = MagicMock()
		mock_api.getListingsByShop.return_value = (0, [])
		mock_api_class.return_value = mock_api

		self.shop.import_listings(listing_state="all", etsy_api=mock_api)

		# Should have been called once for each state
		self.assertEqual(mock_api.getListingsByShop.call_count, len(LISTING_STATES))

	def test_get_oauth2_session_init(self):
		"""get_oauth2_session with init=True returns session without token."""
		self.shop.client_id = "test-client-id"
		session = self.shop.get_oauth2_session(init=True)
		self.assertIsNotNone(session)

	def test_listing_states_constant(self):
		"""LISTING_STATES contains the expected values."""
		self.assertEqual(LISTING_STATES, ("active", "inactive", "sold_out", "draft", "expired"))


class TestEtsyShopWhitelistedFunctions(FrappeTestCase):
	"""Tests for module-level whitelisted functions."""

	def setUp(self):
		self.shop = create_etsy_shop()

	def tearDown(self):
		frappe.delete_doc("Etsy Shop", self.shop.name, force=True)
		frappe.db.commit()

	def test_has_token_returns_false_for_new_shop(self):
		"""has_token returns False for a shop without an access token."""
		result = has_token(self.shop.name)
		self.assertFalse(result)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyShop.get_oauth2_session")
	def test_enqueue_import_listings(self, mock_session):
		"""enqueue_import_listings calls frappe.enqueue with correct params."""
		with patch("frappe.enqueue") as mock_enqueue:
			self.shop.enqueue_import_listings(listing_state="active")
			mock_enqueue.assert_called_once()
			call_kwargs = mock_enqueue.call_args
			self.assertEqual(
				call_kwargs.kwargs.get("etsy_shop") or call_kwargs[1].get("etsy_shop"),
				self.shop.name,
			)

	@patch("etsy.etsy.doctype.etsy_shop.etsy_shop.EtsyShop.get_oauth2_session")
	def test_enqueue_import_receipts(self, mock_session):
		"""enqueue_import_receipts calls frappe.enqueue with correct params."""
		with patch("frappe.enqueue") as mock_enqueue:
			self.shop.enqueue_import_receipts()
			mock_enqueue.assert_called_once()
			call_kwargs = mock_enqueue.call_args
			self.assertEqual(
				call_kwargs.kwargs.get("etsy_shop") or call_kwargs[1].get("etsy_shop"),
				self.shop.name,
			)
