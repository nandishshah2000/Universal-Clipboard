import pytest
from app import app

# Create a fake browser client for testing
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test 1: Does the main website load?
def test_homepage_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Universal Clipboard" in response.data

# Test 2: Is the PWA Manifest serving correctly?
def test_manifest_loads(client):
    response = client.get('/manifest.json')
    assert response.status_code == 200
    assert b"Universal Clipboard" in response.data

# Test 3: Does it successfully block bad URLs?
def test_404_error(client):
    response = client.get('/this-page-does-not-exist')
    assert response.status_code == 404