# Development

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

### Development Commands

Navigate to your bench directory for all commands:

```bash
cd /workspace/development/frappe-bench
```

#### Install/Uninstall App

```bash
# Install
bench --site development.localhost install-app etsy

# Uninstall (without backup)
bench --site development.localhost uninstall-app etsy --no-backup
```

#### Run Tests

```bash
# Run all tests for the app
bench run-tests --app etsy

# Run a specific test module
bench run-tests --app etsy --module etsy.etsy.doctype.etsy_shop.test_etsy_shop

# Run with coverage
bench run-tests --app etsy --coverage
```

#### Build Assets

```bash
# Build all assets
bench build --app etsy

# Watch for changes (during development)
bench watch
```

#### Run Linters

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run Ruff linter only
ruff check etsy/

# Auto-fix issues
ruff check --fix etsy/
```

#### Database Migrations

After changing doctype schemas:

```bash
bench migrate
```

#### Console Access

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

**Configuration:** `.ruff.toml` or `pyproject.toml`

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

**Configuration:** `.eslintrc.json` and `.prettierrc`

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

### Running Tests

```bash
# All tests
bench run-tests --app etsy

# Specific test
bench run-tests --app etsy --module etsy.etsy.doctype.etsy_shop.test_etsy_shop

# Specific test class
bench run-tests --app etsy --test TestEtsyShop

# With verbose output
bench run-tests --app etsy --verbose

# With coverage report
bench run-tests --app etsy --coverage
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

## Contributing

### Contribution Workflow

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

## Architecture Decisions

### Why Pydantic?

- **Type Safety**: Validates API responses at runtime
- **Auto Documentation**: Models serve as documentation
- **IDE Support**: Better autocomplete and type hints
- **Serialization**: Easy conversion to/from JSON

### Why One-Way Sync?

- **Simplicity**: Avoids complex conflict resolution
- **Safety**: Prevents accidental overwrites on Etsy
- **Etsy as Source**: Etsy remains the authoritative source

### Why Per-Record Error Handling?

- **Resilience**: One bad record doesn't stop entire sync
- **Auditability**: Each error is logged individually
- **Recovery**: Failed records can be retried independently

### Why Rate Limiting?

- **Respect API Limits**: Etsy has rate limits
- **Avoid Bans**: Excessive requests can lead to temporary bans
- **Politeness**: Good API citizenship

## Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Example: `1.2.3`

### Creating a Release

1. **Update Version**
   - Update version in `setup.py`
   - Update version in `hooks.py` (if applicable)

2. **Update Changelog**
   - Document all changes since last release
   - Categorize: Added, Changed, Fixed, Removed

3. **Tag Release**
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

4. **GitHub Release**
   - Create release on GitHub
   - Attach changelog
   - Publish

### Changelog Format

```markdown
## [1.2.3] - 2026-02-12

### Added
- New feature X
- Support for Y

### Changed
- Improved Z

### Fixed
- Bug in A
- Issue with B

### Removed
- Deprecated feature C
```

## Resources

### Documentation
- **Frappe Framework**: [frappeframework.com/docs](https://frappeframework.com/docs)
- **ERPNext**: [docs.erpnext.com](https://docs.erpnext.com)
- **Etsy API**: [developer.etsy.com](https://developer.etsy.com)
- **Pydantic**: [docs.pydantic.dev](https://docs.pydantic.dev)

### Community
- **Frappe Forum**: [discuss.frappe.io](https://discuss.frappe.io)
- **GitHub Issues**: [github.com/maeurerdev/erpnext-etsy/issues](https://github.com/maeurerdev/erpnext-etsy/issues)
- **ERPNext Community**: [community.erpnext.com](https://community.erpnext.com)

### Tools
- **Ruff**: [docs.astral.sh/ruff](https://docs.astral.sh/ruff)
- **Pre-commit**: [pre-commit.com](https://pre-commit.com)
- **MkDocs**: [mkdocs.org](https://mkdocs.org)
- **Material for MkDocs**: [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material)

## License

This project is licensed under the GNU General Public License v3 (GPL-3.0).

### GPL-3.0 Summary

- **Freedom to Use**: Use the software for any purpose
- **Freedom to Study**: Access and study the source code
- **Freedom to Modify**: Modify the software
- **Freedom to Distribute**: Share copies and modifications
- **Copyleft**: Derivative works must also be GPL-3.0

See the [LICENSE](https://github.com/maeurerdev/erpnext-etsy/blob/main/LICENSE) file for full details.

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

### Feature Requests

Open a feature request on GitHub Issues:

**Template:**
- **Problem**: What problem does this solve?
- **Solution**: Proposed solution
- **Alternatives**: Other approaches considered
- **Use Case**: Specific use case

### Discussion

For general discussion:
- **Frappe Forum**: Tag with "etsy" and "integration"
- **GitHub Discussions**: (if enabled)

## Next Steps

- **[API Reference](api-reference.md)** - Technical API documentation
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Configuration](configuration.md)** - Detailed configuration guide
