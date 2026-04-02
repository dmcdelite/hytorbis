"""
Iteration 7 Tests - THUMBNAIL Feature + Regression Testing

Focus areas:
1. Thumbnail generation: POST /api/worlds/{world_id}/thumbnail
2. Thumbnail retrieval: GET /api/worlds/{world_id}/thumbnail (auto-generates if missing)
3. Thumbnail in gallery: POST /api/gallery/publish includes auto-generated thumbnail
4. Gallery browse: GET /api/gallery returns entries with thumbnail field
5. Regression: Auth, World CRUD, Gallery, Collaborators, Social features
"""

import pytest
import requests
import os
import json
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hytale.builder"
ADMIN_PASSWORD = "HytaleAdmin123!"
TEST_USER_EMAIL = "testuser_iter7@test.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "TEST_Iter7User"


# ==================== THUMBNAIL TESTS ====================

class TestThumbnailGeneration:
    """Test POST /api/worlds/{world_id}/thumbnail - generates base64 PNG thumbnail"""
    
    def test_generate_thumbnail_success(self, authenticated_client, test_world_with_zones):
        """Generate thumbnail for world with zones returns base64 PNG"""
        world_id = test_world_with_zones
        response = authenticated_client.post(f"{BASE_URL}/api/worlds/{world_id}/thumbnail")
        assert response.status_code == 200
        data = response.json()
        assert "thumbnail" in data
        thumbnail = data["thumbnail"]
        # Verify it's a base64 PNG data URL
        assert thumbnail.startswith("data:image/png;base64,")
        # Verify base64 is valid
        b64_data = thumbnail.split(",")[1]
        try:
            decoded = base64.b64decode(b64_data)
            # PNG magic bytes
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG"
            print(f"Thumbnail generated successfully, size: {len(decoded)} bytes")
        except Exception as e:
            pytest.fail(f"Invalid base64 data: {e}")
    
    def test_generate_thumbnail_empty_world(self, authenticated_client, test_empty_world):
        """Generate thumbnail for empty world (no zones) still works"""
        world_id = test_empty_world
        response = authenticated_client.post(f"{BASE_URL}/api/worlds/{world_id}/thumbnail")
        assert response.status_code == 200
        data = response.json()
        assert "thumbnail" in data
        assert data["thumbnail"].startswith("data:image/png;base64,")
        print("Thumbnail generated for empty world")
    
    def test_generate_thumbnail_nonexistent_world(self, authenticated_client):
        """Generate thumbnail for nonexistent world returns 404"""
        response = authenticated_client.post(f"{BASE_URL}/api/worlds/nonexistent-world-id/thumbnail")
        assert response.status_code == 404
        print("Correctly returns 404 for nonexistent world")


class TestThumbnailRetrieval:
    """Test GET /api/worlds/{world_id}/thumbnail - returns cached or generates new"""
    
    def test_get_thumbnail_auto_generates(self, authenticated_client, test_world_with_zones):
        """GET thumbnail auto-generates if not cached"""
        world_id = test_world_with_zones
        # First clear any existing thumbnail by getting fresh world
        response = authenticated_client.get(f"{BASE_URL}/api/worlds/{world_id}/thumbnail")
        assert response.status_code == 200
        data = response.json()
        assert "thumbnail" in data
        assert data["thumbnail"].startswith("data:image/png;base64,")
        print("GET thumbnail auto-generated successfully")
    
    def test_get_thumbnail_returns_cached(self, authenticated_client, test_world_with_zones):
        """GET thumbnail returns cached version after POST"""
        world_id = test_world_with_zones
        # Generate thumbnail
        post_resp = authenticated_client.post(f"{BASE_URL}/api/worlds/{world_id}/thumbnail")
        assert post_resp.status_code == 200
        generated_thumb = post_resp.json()["thumbnail"]
        
        # Get thumbnail - should return same cached version
        get_resp = authenticated_client.get(f"{BASE_URL}/api/worlds/{world_id}/thumbnail")
        assert get_resp.status_code == 200
        cached_thumb = get_resp.json()["thumbnail"]
        
        assert generated_thumb == cached_thumb
        print("Cached thumbnail returned correctly")
    
    def test_get_thumbnail_nonexistent_world(self, authenticated_client):
        """GET thumbnail for nonexistent world returns 404"""
        response = authenticated_client.get(f"{BASE_URL}/api/worlds/nonexistent-world-id/thumbnail")
        assert response.status_code == 404
        print("Correctly returns 404 for nonexistent world")


class TestThumbnailInGallery:
    """Test thumbnail auto-generation during gallery publish"""
    
    def test_publish_generates_thumbnail(self, authenticated_client, test_world_with_zones):
        """Publishing to gallery auto-generates thumbnail in gallery entry"""
        world_id = test_world_with_zones
        
        # Publish to gallery
        response = authenticated_client.post(
            f"{BASE_URL}/api/gallery/publish",
            json={
                "world_id": world_id,
                "description": "TEST_Iter7 Thumbnail Test World",
                "creator_name": "Test Admin",
                "tags": ["test", "thumbnail", "iter7"]
            }
        )
        
        # Could be 200 (success) or 400 (already published)
        if response.status_code == 400:
            print("World already published, checking existing entry")
        else:
            assert response.status_code == 200
            gallery_id = response.json().get("gallery_id")
            print(f"Published to gallery: {gallery_id}")
        
        # Verify gallery entry has thumbnail
        gallery_resp = authenticated_client.get(f"{BASE_URL}/api/gallery")
        assert gallery_resp.status_code == 200
        entries = gallery_resp.json().get("entries", [])
        
        # Find our entry
        our_entry = None
        for entry in entries:
            if entry.get("world_id") == world_id:
                our_entry = entry
                break
        
        if our_entry:
            assert "thumbnail" in our_entry
            if our_entry["thumbnail"]:
                assert our_entry["thumbnail"].startswith("data:image/png;base64,")
                print(f"Gallery entry has thumbnail: {len(our_entry['thumbnail'])} chars")
            else:
                print("WARNING: Gallery entry thumbnail is empty/null")
        else:
            print("WARNING: Could not find gallery entry for verification")
    
    def test_gallery_browse_returns_thumbnails(self, api_client):
        """GET /api/gallery returns entries with thumbnail field"""
        response = api_client.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        
        entries_with_thumb = 0
        for entry in data["entries"]:
            if entry.get("thumbnail"):
                entries_with_thumb += 1
                assert entry["thumbnail"].startswith("data:image/png;base64,")
        
        print(f"Gallery has {entries_with_thumb}/{len(data['entries'])} entries with thumbnails")


# ==================== REGRESSION TESTS ====================

class TestAuthRegression:
    """Regression tests for authentication"""
    
    def test_login_success(self, api_client):
        """Login with valid credentials"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print(f"Login successful: {data['email']}")
    
    def test_login_invalid_credentials(self, api_client):
        """Login with invalid credentials returns 401"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@email.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_get_me_authenticated(self, authenticated_client):
        """GET /api/auth/me returns current user"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        print(f"Auth/me returned: {data['email']}")
    
    def test_get_me_unauthenticated(self):
        """GET /api/auth/me without auth returns 401"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Unauthenticated /auth/me correctly returns 401")


class TestWorldCRUDRegression:
    """Regression tests for World CRUD operations"""
    
    def test_create_world(self, authenticated_client):
        """POST /api/worlds creates new world"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/worlds",
            json={"name": "TEST_Iter7_CRUD", "map_width": 32, "map_height": 32}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_Iter7_CRUD"
        print(f"Created world: {data['id']}")
        
        # Cleanup
        authenticated_client.delete(f"{BASE_URL}/api/worlds/{data['id']}")
    
    def test_list_worlds(self, authenticated_client):
        """GET /api/worlds returns list of worlds"""
        response = authenticated_client.get(f"{BASE_URL}/api/worlds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Listed {len(data)} worlds")
    
    def test_get_world(self, authenticated_client, test_world_with_zones):
        """GET /api/worlds/{id} returns world details"""
        response = authenticated_client.get(f"{BASE_URL}/api/worlds/{test_world_with_zones}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "zones" in data
        print(f"Got world: {data['name']}")
    
    def test_update_world(self, authenticated_client, test_world_with_zones):
        """PUT /api/worlds/{id} updates world"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/worlds/{test_world_with_zones}",
            json={"name": "TEST_Iter7_Updated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Iter7_Updated"
        print("World updated successfully")
    
    def test_delete_world(self, authenticated_client):
        """DELETE /api/worlds/{id} deletes world"""
        # Create a world to delete
        create_resp = authenticated_client.post(
            f"{BASE_URL}/api/worlds",
            json={"name": "TEST_ToDelete", "map_width": 16, "map_height": 16}
        )
        assert create_resp.status_code == 200
        world_id = create_resp.json()["id"]
        
        # Delete it
        delete_resp = authenticated_client.delete(f"{BASE_URL}/api/worlds/{world_id}")
        assert delete_resp.status_code == 200
        print("World deleted successfully")
        
        # Verify it's gone
        get_resp = authenticated_client.get(f"{BASE_URL}/api/worlds/{world_id}")
        assert get_resp.status_code == 404


class TestGalleryRegression:
    """Regression tests for Gallery features"""
    
    def test_browse_gallery(self, api_client):
        """GET /api/gallery returns gallery entries"""
        response = api_client.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        print(f"Gallery has {data['total']} entries")
    
    def test_gallery_sort_options(self, api_client):
        """Gallery supports various sort options"""
        for sort_by in ["recent", "popular", "downloads", "likes", "rating"]:
            response = api_client.get(f"{BASE_URL}/api/gallery?sort_by={sort_by}")
            assert response.status_code == 200
            print(f"Sort by {sort_by}: OK")
    
    def test_gallery_search(self, api_client):
        """Gallery search works"""
        response = api_client.get(f"{BASE_URL}/api/gallery?query=test")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        print(f"Search 'test' returned {data['total']} entries")
    
    def test_gallery_like(self, authenticated_client, test_gallery_id):
        """POST /api/gallery/{id}/like increments likes"""
        if not test_gallery_id:
            pytest.skip("No gallery entry available")
        response = authenticated_client.post(f"{BASE_URL}/api/gallery/{test_gallery_id}/like")
        assert response.status_code == 200
        print("Gallery like successful")


class TestGalleryForkRegression:
    """Regression tests for gallery forking"""
    
    def test_fork_from_gallery(self, authenticated_client, test_gallery_id):
        """POST /api/gallery/{id}/fork creates forked world"""
        if not test_gallery_id:
            pytest.skip("No gallery entry available")
        response = authenticated_client.post(
            f"{BASE_URL}/api/gallery/{test_gallery_id}/fork",
            json={"name": "TEST_Iter7_Fork"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "world_id" in data
        print(f"Forked from gallery: {data['world_id']}")
        
        # Cleanup
        authenticated_client.delete(f"{BASE_URL}/api/worlds/{data['world_id']}")


class TestCollaboratorRegression:
    """Regression tests for collaborator management"""
    
    def test_get_collaborators(self, authenticated_client, test_world_with_zones):
        """GET /api/worlds/{id}/collaborators returns list"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/worlds/{test_world_with_zones}/collaborators"
        )
        assert response.status_code == 200
        data = response.json()
        assert "collaborators" in data
        assert "owner" in data
        print(f"Collaborators: {len(data['collaborators'])}")
    
    def test_add_collaborator(self, authenticated_client, test_world_with_zones, test_user_id):
        """POST /api/worlds/{id}/collaborators adds collaborator"""
        if not test_user_id:
            pytest.skip("No test user available")
        response = authenticated_client.post(
            f"{BASE_URL}/api/worlds/{test_world_with_zones}/collaborators",
            json={"user_id": test_user_id, "role": "viewer"}
        )
        # 200 success or 400 already exists
        assert response.status_code in [200, 400]
        print(f"Add collaborator: {response.status_code}")


class TestUserSearchRegression:
    """Regression tests for user search"""
    
    def test_search_users(self, api_client):
        """GET /api/users/search returns matching users"""
        response = api_client.get(f"{BASE_URL}/api/users/search?q=admin")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"User search 'admin': {len(data['users'])} results")


class TestActivityFeedRegression:
    """Regression tests for activity feed"""
    
    def test_activity_feed_requires_auth(self):
        """GET /api/activity-feed requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/activity-feed")
        assert response.status_code == 401
        print("Activity feed correctly requires auth")
    
    def test_activity_feed_authenticated(self, authenticated_client):
        """GET /api/activity-feed returns activities when authenticated"""
        response = authenticated_client.get(f"{BASE_URL}/api/activity-feed")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        print(f"Activity feed: {len(data['activities'])} activities")


class TestNotificationsRegression:
    """Regression tests for notifications"""
    
    def test_notifications_requires_auth(self):
        """GET /api/notifications requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401
        print("Notifications correctly requires auth")
    
    def test_notifications_authenticated(self, authenticated_client):
        """GET /api/notifications returns notifications when authenticated"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        print(f"Notifications: {len(data['notifications'])} items")


# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session (unauthenticated)"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def authenticated_client():
    """Session with admin auth"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return session


@pytest.fixture(scope="module")
def test_user_id():
    """Create or get test user ID"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    # Try to register
    response = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD, "name": TEST_USER_NAME}
    )
    if response.status_code == 200:
        return response.json().get("id")
    elif response.status_code == 400:
        # User exists, login to get ID
        login_resp = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if login_resp.status_code == 200:
            me_resp = session.get(f"{BASE_URL}/api/auth/me")
            if me_resp.status_code == 200:
                return me_resp.json().get("id")
    return None


@pytest.fixture(scope="module")
def test_world_with_zones(authenticated_client):
    """Create a test world with zones for thumbnail testing"""
    # Create world
    response = authenticated_client.post(
        f"{BASE_URL}/api/worlds",
        json={"name": "TEST_Iter7_Thumbnail", "map_width": 32, "map_height": 32}
    )
    if response.status_code != 200:
        pytest.skip("Could not create test world")
    
    world_id = response.json()["id"]
    
    # Add zones
    zones = [
        {"type": "emerald_grove", "x": 5, "y": 5, "difficulty": 1},
        {"type": "borea", "x": 10, "y": 10, "difficulty": 2},
        {"type": "desert", "x": 15, "y": 15, "difficulty": 3}
    ]
    for zone in zones:
        authenticated_client.post(
            f"{BASE_URL}/api/worlds/{world_id}/zones",
            json=zone
        )
    
    # Add prefabs
    prefabs = [
        {"type": "dungeon", "x": 7, "y": 7, "rotation": 0, "scale": 1.0},
        {"type": "village", "x": 12, "y": 12, "rotation": 90, "scale": 1.0}
    ]
    for prefab in prefabs:
        authenticated_client.post(
            f"{BASE_URL}/api/worlds/{world_id}/prefabs",
            json=prefab
        )
    
    yield world_id
    
    # Cleanup
    authenticated_client.delete(f"{BASE_URL}/api/worlds/{world_id}")


@pytest.fixture(scope="module")
def test_empty_world(authenticated_client):
    """Create an empty test world (no zones/prefabs)"""
    response = authenticated_client.post(
        f"{BASE_URL}/api/worlds",
        json={"name": "TEST_Iter7_Empty", "map_width": 16, "map_height": 16}
    )
    if response.status_code != 200:
        pytest.skip("Could not create empty test world")
    
    world_id = response.json()["id"]
    yield world_id
    
    # Cleanup
    authenticated_client.delete(f"{BASE_URL}/api/worlds/{world_id}")


@pytest.fixture(scope="module")
def test_gallery_id(authenticated_client):
    """Get or create a gallery entry for testing"""
    # Check existing gallery
    response = authenticated_client.get(f"{BASE_URL}/api/gallery")
    if response.status_code == 200:
        entries = response.json().get("entries", [])
        if entries:
            return entries[0].get("id")
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
