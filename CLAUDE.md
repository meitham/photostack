# AI Agent Conventions

## Documentation

- Documentation lives in `docs/` and uses MkDocs with Material theme
- **IMPORTANT**: When adding new features or changing existing ones, update the relevant docs
- Documentation structure:
  - `docs/getting-started/` - Installation, quickstart, configuration
  - `docs/cli/` - CLI command reference
  - `docs/api/` - Python API reference
  - `docs/development/` - Contributing, testing
- Update `mkdocs.yml` if adding new pages
- Build docs locally with: `mkdocs serve`

## Testing with pytest

### Structure

- NEVER use test classes, always use test functions
- Tests follow the **given-when-then** pattern

### Given-When-Then Style

```python
def test_user_can_login(authenticated_user, client):
    # given: authenticated_user fixture provides a valid user (see conftest.py)

    # when: user attempts to login
    response = client.post('/login', data={'user': authenticated_user.name})

    # then: login succeeds
    assert response.status_code == 200
    assert response.json()['logged_in'] is True
```

### Fixture Naming Convention

- Common fixtures belong in `conftest.py`
- Fixture function name: `fixture_<name>`
- Fixture decorator must set `name='<name>'`

```python
# CORRECT
@pytest.fixture(name='user')
def fixture_user():
    return User(name='test')

# WRONG - do not do this
@pytest.fixture
def user():
    return User(name='test')
```

### Parametrized Tests

- Use `@pytest.mark.parametrize` for testing multiple cases of similar logic
- Use `pytest.param()` with `id=` to keep test ID inline with its data
- Group related test cases into a single parametrized test

```python
# CORRECT - parametrized with pytest.param and inline ids
@pytest.mark.parametrize(
    'input_email,expected_canon',
    [
        pytest.param('John.Doe@Gmail.com', 'johndoe@gmail.com', id='gmail-dots-removed'),
        pytest.param('user+tag@example.com', 'user@example.com', id='plus-addressing-stripped'),
        pytest.param('test@googlemail.com', 'test@gmail.com', id='googlemail-alias'),
    ],
)
def test_normalize_email(input_email, expected_canon):
    # given: an email address (provided by parametrize)

    # when: normalizing the email
    result = normalize_email(input_email)

    # then: canonical form matches expected
    assert result.canon == expected_canon


# WRONG - ids list at end (harder to maintain, id not next to data)
@pytest.mark.parametrize(
    'input_email,expected_canon',
    [
        ('John.Doe@Gmail.com', 'johndoe@gmail.com'),
        ('user+tag@example.com', 'user@example.com'),
    ],
    ids=['gmail-dots-removed', 'plus-addressing-stripped'],
)

# WRONG - separate functions for each case
def test_normalize_email_basic():
    result = normalize_email('John.Doe@Gmail.com')
    assert result.canon == 'johndoe@gmail.com'
```

### Mocking

- Prefer `pytest` `monkeypatch` over `unittest.mock` / `mock` library
- Mocks should be set up in fixtures, NOT inline in test functions

```python
# CORRECT - mock in fixture
@pytest.fixture(name='mock_api')
def fixture_mock_api(monkeypatch):
    """Given: API calls are mocked."""
    responses = {}
    def mock_get(url):
        return responses.get(url, {'error': 'not found'})
    monkeypatch.setattr('mymodule.api.get', mock_get)
    return responses

def test_fetches_user(mock_api):
    # given: API returns user data
    mock_api['/users/1'] = {'name': 'Alice'}

    # when: we fetch the user
    user = fetch_user(1)

    # then: user is returned
    assert user['name'] == 'Alice'


# WRONG - do not mock inline in tests
def test_fetches_user_bad(monkeypatch):
    monkeypatch.setattr('mymodule.api.get', lambda url: {'name': 'Alice'})
    user = fetch_user(1)
    assert user['name'] == 'Alice'
```

### Example conftest.py

```python
import pytest

@pytest.fixture(name='config')
def fixture_config():
    """Given: a default configuration."""
    return {'debug': True}

@pytest.fixture(name='client')
def fixture_client(config):
    """Given: an HTTP client with config applied."""
    return Client(config)

@pytest.fixture(name='mock_datetime')
def fixture_mock_datetime(monkeypatch):
    """Given: datetime.now() returns a fixed time."""
    import datetime
    fixed = datetime.datetime(2024, 1, 1, 12, 0, 0)
    monkeypatch.setattr('datetime.datetime', lambda: fixed)
    return fixed
```
