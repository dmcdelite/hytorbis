"""
Regression Test Suite for Hytale World Builder - Post-Refactoring
Tests all backend APIs after major refactoring:
- Modular routers (auth, users, worlds, ai, gallery, reviews, versions, misc)
- Social features (follow/unfollow, notifications)
- Enhanced permissions (world ownership)
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hytale-base.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@hytale.builder"
ADMIN_PASSWORD = "HytaleAdmin123!"


class TestHealthAndBasics:
    """Health check and basic API tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✓ Health endpoint working")
    
    def test_root_endpoint(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        print("✓ Root endpoint working")


class TestAuthentication:
    """Auth endpoints: register, login, me, logout"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def test_admin_login_success(self):
        """POST /api/auth/login with admin credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert "id" in data
        # Check cookies are set
        assert "access_token" in self.session.cookies or response.cookies.get("access_token")
        print(f"✓ Admin login successful: {data['name']}")
        return data
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected with 401")
    
    def test_get_me_authenticated(self):
        """GET /api/auth/me returns user when authenticated"""
        # Login first
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print("✓ GET /api/auth/me returns authenticated user")
    
    def test_get_me_unauthenticated(self):
        """GET /api/auth/me returns 401 when not authenticated"""
        new_session = requests.Session()
        response = new_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ GET /api/auth/me returns 401 when unauthenticated")
    
    def test_register_new_user(self):
        """POST /api/auth/register creates new user"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
        assert data["name"] == "Test User"
        assert "id" in data
        print(f"✓ User registered: {unique_email}")
        return data
    
    def test_register_duplicate_email(self):
        """POST /api/auth/register with existing email returns 400"""
        response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "TestPass123!",
            "name": "Duplicate"
        })
        assert response.status_code == 400
        print("✓ Duplicate email registration rejected")
    
    def test_logout(self):
        """POST /api/auth/logout clears session"""
        # Login first
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        response = self.session.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        # Verify logged out
        me_response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 401
        print("✓ Logout successful")


class TestWorldsCRUD:
    """World CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        # Login as admin
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_list_worlds(self):
        """GET /api/worlds returns list of worlds"""
        response = self.session.get(f"{BASE_URL}/api/worlds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} worlds")
    
    def test_create_world(self):
        """POST /api/worlds creates new world"""
        world_name = f"Test World {uuid.uuid4().hex[:6]}"
        response = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": world_name,
            "map_width": 32,
            "map_height": 32
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == world_name
        assert "id" in data
        assert "seed" in data
        assert data["map_width"] == 32
        print(f"✓ Created world: {world_name}")
        return data
    
    def test_get_world_by_id(self):
        """GET /api/worlds/{id} returns world details"""
        # Create a world first
        create_resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Get Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = create_resp.json()["id"]
        
        response = self.session.get(f"{BASE_URL}/api/worlds/{world_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == world_id
        print(f"✓ Retrieved world by ID: {world_id}")
    
    def test_update_world(self):
        """PUT /api/worlds/{id} updates world"""
        # Create a world first
        create_resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Update Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = create_resp.json()["id"]
        
        new_name = f"Updated World {uuid.uuid4().hex[:6]}"
        response = self.session.put(f"{BASE_URL}/api/worlds/{world_id}", json={
            "name": new_name
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        print(f"✓ Updated world: {new_name}")
    
    def test_delete_world(self):
        """DELETE /api/worlds/{id} deletes world"""
        # Create a world first
        create_resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Delete Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = create_resp.json()["id"]
        
        response = self.session.delete(f"{BASE_URL}/api/worlds/{world_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_resp = self.session.get(f"{BASE_URL}/api/worlds/{world_id}")
        assert get_resp.status_code == 404
        print(f"✓ Deleted world: {world_id}")


class TestTemplates:
    """Template endpoints"""
    
    def test_get_templates(self):
        """GET /api/templates returns available templates"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 1
        print(f"✓ Retrieved {len(data['templates'])} templates")
    
    def test_create_from_template(self):
        """POST /api/worlds/from-template creates world from template"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Get templates first
        templates_resp = requests.get(f"{BASE_URL}/api/templates")
        templates = templates_resp.json()["templates"]
        template_id = templates[0]["id"]
        
        response = session.post(f"{BASE_URL}/api/worlds/from-template", json={
            "name": f"Template World {uuid.uuid4().hex[:6]}",
            "template": template_id,
            "map_width": 32,
            "map_height": 32
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert len(data.get("zones", [])) > 0 or len(data.get("prefabs", [])) > 0
        print(f"✓ Created world from template: {template_id}")


class TestExports:
    """Export endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        # Create a test world
        resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Export Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        self.world_id = resp.json()["id"]
    
    def test_export_json(self):
        """GET /api/worlds/{id}/export/json returns JSON export"""
        response = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/export/json")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "world" in data
        print("✓ JSON export working")
    
    def test_export_hytale(self):
        """GET /api/worlds/{id}/export/hytale returns Hytale format"""
        response = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/export/hytale")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "hytale"
        assert "config" in data
        assert "worldgen" in data["config"]
        print("✓ Hytale export working")
    
    def test_export_prefab(self):
        """GET /api/worlds/{id}/export/prefab returns prefab format"""
        response = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/export/prefab")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "prefab.json"
        assert "data" in data
        print("✓ Prefab export working")
    
    def test_export_jar(self):
        """GET /api/worlds/{id}/export/jar returns JAR package"""
        response = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/export/jar")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "jar"
        assert "data_base64" in data
        assert "filename" in data
        print("✓ JAR export working")


class TestGallery:
    """Gallery endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_browse_gallery(self):
        """GET /api/gallery returns gallery entries"""
        response = self.session.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        print(f"✓ Gallery has {data['total']} entries")
    
    def test_publish_to_gallery(self):
        """POST /api/gallery/publish publishes world"""
        # Create a world first
        world_resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Publish Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = world_resp.json()["id"]
        
        response = self.session.post(f"{BASE_URL}/api/gallery/publish", json={
            "world_id": world_id,
            "description": "Test world for gallery",
            "creator_name": "Test Admin",
            "tags": ["test", "regression"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "gallery_id" in data
        print(f"✓ Published to gallery: {data['gallery_id']}")
        return data["gallery_id"]
    
    def test_like_gallery_entry(self):
        """POST /api/gallery/{id}/like increments likes"""
        # Get existing gallery entries
        gallery_resp = self.session.get(f"{BASE_URL}/api/gallery")
        entries = gallery_resp.json()["entries"]
        
        if entries:
            entry_id = entries[0]["id"]
            response = self.session.post(f"{BASE_URL}/api/gallery/{entry_id}/like")
            assert response.status_code == 200
            print(f"✓ Liked gallery entry: {entry_id}")
        else:
            pytest.skip("No gallery entries to like")
    
    def test_download_from_gallery(self):
        """POST /api/gallery/{id}/download returns world data"""
        gallery_resp = self.session.get(f"{BASE_URL}/api/gallery")
        entries = gallery_resp.json()["entries"]
        
        if entries:
            entry_id = entries[0]["id"]
            response = self.session.post(f"{BASE_URL}/api/gallery/{entry_id}/download")
            assert response.status_code == 200
            data = response.json()
            assert "world" in data
            print(f"✓ Downloaded from gallery: {entry_id}")
        else:
            pytest.skip("No gallery entries to download")


class TestReviews:
    """Review endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_reviews(self):
        """GET /api/reviews/{gallery_id} returns reviews"""
        # Get a gallery entry
        gallery_resp = self.session.get(f"{BASE_URL}/api/gallery")
        entries = gallery_resp.json()["entries"]
        
        if entries:
            gallery_id = entries[0]["id"]
            response = self.session.get(f"{BASE_URL}/api/reviews/{gallery_id}")
            assert response.status_code == 200
            data = response.json()
            assert "reviews" in data
            print(f"✓ Retrieved reviews for gallery: {gallery_id}")
        else:
            pytest.skip("No gallery entries for review test")
    
    def test_create_review(self):
        """POST /api/reviews creates review (requires auth)"""
        # Create a new user to avoid duplicate review error
        unique_email = f"reviewer_{uuid.uuid4().hex[:8]}@test.com"
        reviewer_session = requests.Session()
        reviewer_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Reviewer"
        })
        
        # Get a gallery entry
        gallery_resp = reviewer_session.get(f"{BASE_URL}/api/gallery")
        entries = gallery_resp.json()["entries"]
        
        if entries:
            gallery_id = entries[0]["id"]
            response = reviewer_session.post(f"{BASE_URL}/api/reviews", json={
                "gallery_id": gallery_id,
                "rating": 5,
                "comment": "Great world! Testing regression."
            })
            assert response.status_code == 200
            data = response.json()
            assert "review_id" in data
            print(f"✓ Created review for gallery: {gallery_id}")
        else:
            pytest.skip("No gallery entries for review creation")


class TestVersions:
    """Version history endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        # Create a test world
        resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Version Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        self.world_id = resp.json()["id"]
    
    def test_create_version(self):
        """POST /api/worlds/{id}/versions creates version snapshot"""
        response = self.session.post(f"{BASE_URL}/api/worlds/{self.world_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        print(f"✓ Created version {data['version']} for world")
    
    def test_list_versions(self):
        """GET /api/worlds/{id}/versions lists versions"""
        # Create a version first
        self.session.post(f"{BASE_URL}/api/worlds/{self.world_id}/versions")
        
        response = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert len(data["versions"]) >= 1
        print(f"✓ Listed {len(data['versions'])} versions")
    
    def test_restore_version(self):
        """POST /api/worlds/{id}/versions/{vid}/restore restores world"""
        # Create a version
        self.session.post(f"{BASE_URL}/api/worlds/{self.world_id}/versions")
        
        # Get versions
        versions_resp = self.session.get(f"{BASE_URL}/api/worlds/{self.world_id}/versions")
        versions = versions_resp.json()["versions"]
        
        if versions:
            version_id = versions[0]["id"]
            response = self.session.post(f"{BASE_URL}/api/worlds/{self.world_id}/versions/{version_id}/restore")
            assert response.status_code == 200
            print(f"✓ Restored version: {version_id}")


class TestVisibility:
    """World visibility toggle"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        # Create a test world
        resp = self.session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Visibility Test {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        self.world_id = resp.json()["id"]
    
    def test_set_private(self):
        """PUT /api/worlds/{id}/visibility?is_public=false sets private"""
        response = self.session.put(f"{BASE_URL}/api/worlds/{self.world_id}/visibility?is_public=false")
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] == False
        print("✓ Set world to private")
    
    def test_set_public(self):
        """PUT /api/worlds/{id}/visibility?is_public=true sets public"""
        response = self.session.put(f"{BASE_URL}/api/worlds/{self.world_id}/visibility?is_public=true")
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] == True
        print("✓ Set world to public")


class TestSocialFeatures:
    """Social features: follow/unfollow, notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Create two users for social testing
        self.user1_session = requests.Session()
        self.user1_email = f"social1_{uuid.uuid4().hex[:8]}@test.com"
        resp1 = self.user1_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.user1_email,
            "password": "TestPass123!",
            "name": "Social User 1"
        })
        self.user1_id = resp1.json()["id"]
        
        self.user2_session = requests.Session()
        self.user2_email = f"social2_{uuid.uuid4().hex[:8]}@test.com"
        resp2 = self.user2_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.user2_email,
            "password": "TestPass123!",
            "name": "Social User 2"
        })
        self.user2_id = resp2.json()["id"]
    
    def test_follow_user(self):
        """POST /api/users/{id}/follow follows user"""
        response = self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/follow")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Followed"
        print(f"✓ User 1 followed User 2")
    
    def test_follow_self_fails(self):
        """POST /api/users/{id}/follow cannot follow self"""
        response = self.user1_session.post(f"{BASE_URL}/api/users/{self.user1_id}/follow")
        assert response.status_code == 400
        print("✓ Cannot follow self (400)")
    
    def test_unfollow_user(self):
        """POST /api/users/{id}/unfollow unfollows user"""
        # Follow first
        self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/follow")
        
        response = self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/unfollow")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unfollowed"
        print("✓ User 1 unfollowed User 2")
    
    def test_get_followers(self):
        """GET /api/users/{id}/followers returns followers list"""
        # Follow first
        self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/follow")
        
        response = self.user2_session.get(f"{BASE_URL}/api/users/{self.user2_id}/followers")
        assert response.status_code == 200
        data = response.json()
        assert "followers" in data
        print(f"✓ User 2 has {len(data['followers'])} followers")
    
    def test_get_following(self):
        """GET /api/users/{id}/following returns following list"""
        # Follow first
        self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/follow")
        
        response = self.user1_session.get(f"{BASE_URL}/api/users/{self.user1_id}/following")
        assert response.status_code == 200
        data = response.json()
        assert "following" in data
        print(f"✓ User 1 is following {len(data['following'])} users")
    
    def test_is_following(self):
        """GET /api/users/{id}/is-following checks follow status"""
        # Follow first
        self.user1_session.post(f"{BASE_URL}/api/users/{self.user2_id}/follow")
        
        response = self.user1_session.get(f"{BASE_URL}/api/users/{self.user2_id}/is-following")
        assert response.status_code == 200
        data = response.json()
        assert data["is_following"] == True
        print("✓ is-following returns True")


class TestNotifications:
    """Notification endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_notifications(self):
        """GET /api/notifications returns notifications"""
        response = self.session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Retrieved {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_mark_all_read(self):
        """POST /api/notifications/read-all marks all as read"""
        response = self.session.post(f"{BASE_URL}/api/notifications/read-all")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All notifications marked as read"
        print("✓ Marked all notifications as read")


class TestUserProfile:
    """User profile endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.user_id = resp.json()["id"]
    
    def test_get_profile(self):
        """GET /api/users/{id}/profile returns profile with stats"""
        response = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/profile")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "worlds_count" in data
        assert "published_count" in data
        assert "followers_count" in data
        assert "following_count" in data
        print(f"✓ Profile: {data['name']}, {data['worlds_count']} worlds, {data['followers_count']} followers")
    
    def test_update_profile(self):
        """PUT /api/users/profile updates profile"""
        new_bio = f"Updated bio at {time.time()}"
        response = self.session.put(f"{BASE_URL}/api/users/profile", json={
            "bio": new_bio
        })
        assert response.status_code == 200
        
        # Verify update
        profile_resp = self.session.get(f"{BASE_URL}/api/users/{self.user_id}/profile")
        assert profile_resp.json()["bio"] == new_bio
        print("✓ Profile updated successfully")


class TestPermissions:
    """Permission tests: world ownership"""
    
    def test_non_owner_cannot_edit_world(self):
        """PUT /api/worlds/{id} fails 403 for non-owners"""
        # User 1 creates a world
        user1_session = requests.Session()
        user1_email = f"owner_{uuid.uuid4().hex[:8]}@test.com"
        user1_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "TestPass123!",
            "name": "Owner"
        })
        
        world_resp = user1_session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Owner's World {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = world_resp.json()["id"]
        
        # User 2 tries to edit
        user2_session = requests.Session()
        user2_email = f"nonowner_{uuid.uuid4().hex[:8]}@test.com"
        user2_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "TestPass123!",
            "name": "Non-Owner"
        })
        
        response = user2_session.put(f"{BASE_URL}/api/worlds/{world_id}", json={
            "name": "Hacked Name"
        })
        assert response.status_code == 403
        print("✓ Non-owner cannot edit world (403)")
    
    def test_non_owner_cannot_delete_world(self):
        """DELETE /api/worlds/{id} fails 403 for non-owners"""
        # User 1 creates a world
        user1_session = requests.Session()
        user1_email = f"delowner_{uuid.uuid4().hex[:8]}@test.com"
        user1_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "TestPass123!",
            "name": "Delete Owner"
        })
        
        world_resp = user1_session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"Protected World {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        world_id = world_resp.json()["id"]
        
        # User 2 tries to delete
        user2_session = requests.Session()
        user2_email = f"delnonowner_{uuid.uuid4().hex[:8]}@test.com"
        user2_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "TestPass123!",
            "name": "Delete Non-Owner"
        })
        
        response = user2_session.delete(f"{BASE_URL}/api/worlds/{world_id}")
        assert response.status_code == 403
        print("✓ Non-owner cannot delete world (403)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
