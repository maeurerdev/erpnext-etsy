# Contributing

This guide covers development setup, code style, testing, and contributing to the Etsy Integration project.

## Development Setup

### Prerequisites

- **Python**: 3.10 or higher
- **Frappe Framework**: Latest compatible version
- **ERPNext**: Version 15
- **Git**: For version control
- **MariaDB/PostgreSQL**: Database
- **Redis**: For caching and background jobs

### Setting Up Development Environment

#### 1. Clone the Repository

```bash
cd /path/to/your/bench
bench get-app https://github.com/maeurerdev/erpnext-etsy --branch develop
```

Or for direct development:

```bash
cd apps
git clone https://github.com/maeurerdev/erpnext-etsy.git etsy
cd ..
```

#### 2. Install the App

```bash
bench --site development.localhost install-app etsy
```

#### 3. Install Development Dependencies

```bash
cd apps/etsy
pip install -e ".[dev]"  # If dev dependencies are defined in setup.py
```

#### 4. Set Up Pre-commit Hooks

The project uses pre-commit hooks for code quality:

```bash
pre-commit install
```

Run hooks manually:

```bash
pre-commit run --all-files
```

## Development Commands

Navigate to your bench directory for all commands:

```bash
cd /workspace/development/frappe-bench
```

### Install/Uninstall App

```bash
# Install
bench --site development.localhost install-app etsy

# Uninstall (without backup)
bench --site development.localhost uninstall-app etsy --no-backup
```

### Run Tests

```bash
# Run all tests for the app
bench run-tests --app etsy

# Run a specific test module
bench run-tests --app etsy --module etsy.etsy.doctype.etsy_shop.test_etsy_shop

# Run a specific test class
bench run-tests --app etsy --test TestEtsyShop

# With verbose output
bench run-tests --app etsy --verbose

# With coverage report
bench run-tests --app etsy --coverage
```

### Build Assets

```bash
# Build all assets
bench build --app etsy

# Watch for changes (during development)
bench watch
```

### Run Linters

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run Ruff linter only
ruff check etsy/

# Auto-fix issues
ruff check --fix etsy/
```

### Database Migrations

After changing doctype schemas:

```bash
bench migrate
```

### Console Access

For debugging and testing:

```bash
bench --site development.localhost console
```

```python
# Example: Test API connection
import frappe
shop = frappe.get_doc("Etsy Shop", "Your Shop Name")
from etsy.api import EtsyAPI
api = EtsyAPI(shop)
print(api.getMe())
```

## Code Style

The project follows strict code style guidelines enforced by linters.

### Python

**Linter:** Ruff

**Rules:**

- **Indentation:** Tabs
- **Quotes:** Double quotes
- **Line Length:** 110 characters
- **Target:** Python 3.10
- **Lint Rules:** F (pyflakes), E (pycodestyle errors), W (pycodestyle warnings), I (isort), UP (pyupgrade), B (flake8-bugbear), RUF (ruff-specific)

**Example:**

```python
def example_function(param1: str, param2: int) -> dict:
	"""
	Docstring with proper formatting.

	Args:
		param1: Description
		param2: Description

	Returns:
		Description of return value
	"""
	result = {
		"key": "value",
		"number": param2,
	}
	return result
```

### JavaScript

**Linter:** ESLint + Prettier

**Rules:**

- **Indentation:** Tabs (size 4)
- **Quotes:** Double quotes preferred
- **Target:** ES2022
- **Naming:** Snake_case acceptable (Frappe convention)

**Example:**

```javascript
frappe.ui.form.on("Etsy Shop", {
	refresh: function(frm) {
		if (frm.doc.status === "Connected") {
			frm.add_custom_button(__("Import Listings"), function() {
				frm.call("import_listings");
			});
		}
	}
});
```

### EditorConfig

The project includes `.editorconfig` for consistent editor settings:

- **Charset:** UTF-8
- **Line Endings:** LF
- **Trim Trailing Whitespace:** Yes
- **Insert Final Newline:** Yes
- **Indentation:** Tabs (except JSON: 2 spaces)

## Project Structure

```
etsy/
├── api.py              # HTTP client and API wrapper
├── datastruct.py       # Pydantic models for Etsy API responses
├── hooks.py            # Frappe hooks and custom fields
├── install.py          # Installation and uninstallation routines
└── etsy/
    └── doctype/
        ├── etsy_shop/        # Main doctype for shop management
        ├── etsy_settings/    # Global sync settings
        └── etsy_listing/     # Per-listing configuration
```

## Testing

### Test Structure

Tests are located in doctype directories:

```
etsy/etsy/doctype/etsy_shop/
├── etsy_shop.py
├── etsy_shop.json
├── etsy_shop.js
└── test_etsy_shop.py    # Test file
```

### Writing Tests

**Example Test:**

```python
import frappe
import unittest

class TestEtsyShop(unittest.TestCase):
	def setUp(self):
		"""Set up test fixtures"""
		self.shop = frappe.get_doc({
			"doctype": "Etsy Shop",
			"shop_name": "Test Shop",
			"company": "_Test Company",
			# ... other required fields
		})
		self.shop.insert()

	def tearDown(self):
		"""Clean up after tests"""
		frappe.delete_doc("Etsy Shop", "Test Shop", force=True)

	def test_shop_creation(self):
		"""Test shop document creation"""
		self.assertEqual(self.shop.shop_name, "Test Shop")
		self.assertEqual(self.shop.status, "Disconnected")

	def test_auth_header_generation(self):
		"""Test OAuth header generation"""
		self.shop.access_token = "test_token"
		header = self.shop.get_auth_header()
		self.assertEqual(header["Authorization"], "Bearer test_token")
```

### Mocking External APIs

For testing API interactions without hitting Etsy:

```python
from unittest.mock import patch, MagicMock

class TestEtsyAPI(unittest.TestCase):
	@patch('etsy.api.SyncCacheClient')
	def test_get_me(self, mock_client):
		"""Test getMe API call"""
		# Mock the response
		mock_response = MagicMock()
		mock_response.json.return_value = {
			"user_id": 12345,
			"login_name": "test_user",
			"primary_email": "test@example.com"
		}
		mock_client.return_value.get.return_value = mock_response

		# Test the API call
		from etsy.api import EtsyAPI
		api = EtsyAPI(self.shop)
		result = api.getMe()

		self.assertEqual(result.user_id, 12345)
```

## Contributing Workflow

1. **Fork the Repository**
   - Fork on GitHub: [maeurerdev/erpnext-etsy](https://github.com/maeurerdev/erpnext-etsy)

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code following style guidelines
   - Add tests for new features
   - Update documentation if needed

4. **Run Tests and Linters**
   ```bash
   pre-commit run --all-files
   bench run-tests --app etsy
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Add new feature description"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Open PR on GitHub
   - Provide clear description
   - Reference any related issues

### Commit Message Convention

Follow conventional commits:

**Format:** `type(scope): description`

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): Add support for listing variants
fix(sync): Handle missing item gracefully
docs(readme): Update installation instructions
test(shop): Add OAuth flow tests
```

### Pull Request Guidelines

**Good PR:**

- Clear, descriptive title
- Detailed description of changes
- References related issues (#123)
- Includes tests for new features
- All tests passing
- Follows code style guidelines
- Updates documentation if needed

**PR Template:**

```markdown
## Description
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
How to test these changes.

## Related Issues
Fixes #123
Related to #456

## Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Debugging

### Enable Debug Mode

In `site_config.json`:

```json
{
	"developer_mode": 1,
	"enable_frappe_logger": 1
}
```

Restart bench:

```bash
bench restart
```

### Logging

Use Frappe's logging:

```python
import frappe

# Info logging
frappe.log("Processing receipt: {0}".format(receipt_id))

# Error logging
frappe.log_error(
	title="Etsy Import Error",
	message=frappe.get_traceback()
)

# Debug logging (when developer_mode is on)
frappe.logger().debug("Debug message")
```

View logs:

```bash
tail -f logs/development.localhost.log
```

### Using pdb

Insert breakpoint:

```python
import pdb; pdb.set_trace()
```

Or with Python 3.7+:

```python
breakpoint()
```

### Browser DevTools

For frontend debugging:

1. Open browser DevTools (F12)
2. Check Console for JavaScript errors
3. Use Network tab to inspect API calls
4. Use Sources tab to debug JavaScript

### Test API Connection

```bash
bench --site [site-name] console
```
```python
from etsy.api import EtsyAPI
shop = frappe.get_doc("Etsy Shop", "Your Shop Name")
api = EtsyAPI(shop)
print(api.get("/application/users/me"))  # Should return user data
exit()
```

### Check Database State

```bash
bench --site [site-name] mariadb
```
```sql
-- Count Etsy-related records
SELECT COUNT(*) FROM `tabCustomer` WHERE etsy_customer_id IS NOT NULL;
SELECT COUNT(*) FROM `tabSales Order` WHERE etsy_order_id IS NOT NULL;
SELECT COUNT(*) FROM `tabEtsy Listing`;
exit;
```

### Review Scheduled Jobs

```bash
bench --site [site-name] console
```
```python
import frappe
jobs = frappe.get_all("Scheduled Job Log",
                       filters={"scheduled_job_type": ["like", "%etsy%"]},
                       fields=["name", "status", "creation"],
                       order_by="creation desc",
                       limit=10)
for job in jobs:
    print(f"{job.creation}: {job.status}")
exit()
```

## Getting Help

### Issues and Bugs

Report issues on GitHub:
[https://github.com/maeurerdev/erpnext-etsy/issues](https://github.com/maeurerdev/erpnext-etsy/issues)

**Include:**

- ERPNext version
- App version (commit hash)
- Detailed error messages
- Steps to reproduce
- Expected vs. actual behavior
