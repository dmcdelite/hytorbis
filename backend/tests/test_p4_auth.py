"""
P4 Backend Tests - Authentication, Profiles, Versions, Visibility, Reviews
Tests for Hytale World Builder Phase 4 features
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hytale-base.preview.emergentagent.com').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@hytale.builder"
ADMIN_PASSWORD = "HytaleAdmin123!"

class TestHealthCheck:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")


class TestAuthEndpoints:
    """P4: Authentication endpoint tests"""
    
    def test_login_with_admin_credentials(self):
        """Test login with admin credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert "name" in data
        print(f"✓ Admin login successful: {data['name']}")
        
        # Verify cookies are set
        assert "access_token" in session.cookies or response.cookies.get("access_token")
        print("✓ Access token cookie set")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_register_new_user(self):
        """Test registering a new user"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Test User"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert data["email"] == unique_email
        assert data["name"] == "Test User"
        assert data["role"] == "user"
        print(f"✓ User registration successful: {unique_email}")
        return data["id"]
    
    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "TestPassword123!",
            "name": "Duplicate User"
        })
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Duplicate email correctly rejected")
    
    def test_get_current_user_authenticated(self):
        """Test GET /api/auth/me with valid session"""
        session = requests.Session()
        # Login first
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        
        # Get current user
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Get me failed: {response.text}"
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ GET /api/auth/me returns user: {data['email']}")
    
    def test_get_current_user_unauthenticated(self):
        """Test GET /api/auth/me without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthenticated /api/auth/me correctly returns 401")
    
    def test_logout(self):
        """Test logout clears cookies"""
        session = requests.Session()
        # Login first
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Logout
        response = session.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        assert response.json().get("message") == "Logged out"
        print("✓ Logout successful")
        
        # Verify can't access protected endpoint
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 401
        print("✓ Session cleared after logout")
    
    def test_refresh_token(self):
        """Test token refresh endpoint"""
        session = requests.Session()
        # Login first
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Refresh token
        response = session.post(f"{BASE_URL}/api/auth/refresh")
        assert response.status_code == 200
        assert response.json().get("message") == "Token refreshed"
        print("✓ Token refresh successful")


class TestUserProfile:
    """P4: User profile endpoint tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        user_id = response.json()["id"]
        return session, user_id
    
    def test_get_user_profile(self, auth_session):
        """Test getting user profile"""
        session, user_id = auth_session
        response = session.get(f"{BASE_URL}/api/users/{user_id}/profile")
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "worlds_count" in data
        assert "published_count" in data
        assert "total_downloads" in data
        assert "total_likes" in data
        print(f"✓ Profile retrieved: {data['name']} - {data['worlds_count']} worlds")
    
    def test_update_profile(self, auth_session):
        """Test updating user profile"""
        session, user_id = auth_session
        new_bio = f"Updated bio at {datetime.now().isoformat()}"
        response = session.put(f"{BASE_URL}/api/users/profile", json={
            "bio": new_bio
        })
        assert response.status_code == 200, f"Update profile failed: {response.text}"
        
        # Verify update
        profile_resp = session.get(f"{BASE_URL}/api/users/{user_id}/profile")
        assert profile_resp.status_code == 200
        assert profile_resp.json()["bio"] == new_bio
        print(f"✓ Profile updated with new bio")
    
    def test_update_profile_unauthenticated(self):
        """Test updating profile without auth fails"""
        response = requests.put(f"{BASE_URL}/api/users/profile", json={
            "bio": "Should fail"
        })
        assert response.status_code == 401
        print("✓ Unauthenticated profile update correctly rejected")


class TestWorldVersions:
    """P4: World version history tests"""
    
    @pytest.fixture
    def auth_session_with_world(self):
        """Create authenticated session and get a world ID"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        # Get existing worlds
        worlds_resp = session.get(f"{BASE_URL}/api/worlds")
        assert worlds_resp.status_code == 200
        worlds = worlds_resp.json()
        
        if worlds:
            world_id = worlds[0]["id"]
        else:
            # Create a world if none exist
            create_resp = session.post(f"{BASE_URL}/api/worlds", json={
                "name": f"Test World {uuid.uuid4().hex[:6]}",
                "map_width": 32,
                "map_height": 32
            })
            assert create_resp.status_code == 200
            world_id = create_resp.json()["id"]
        
        return session, world_id
    
    def test_create_version(self, auth_session_with_world):
        """Test creating a version snapshot"""
        session, world_id = auth_session_with_world
        response = session.post(f"{BASE_URL}/api/worlds/{world_id}/versions")
        assert response.status_code == 200, f"Create version failed: {response.text}"
        data = response.json()
        assert "version" in data
        print(f"✓ Version {data['version']} created for world {world_id}")
    
    def test_list_versions(self, auth_session_with_world):
        """Test listing world versions"""
        session, world_id = auth_session_with_world
        
        # Create a version first
        session.post(f"{BASE_URL}/api/worlds/{world_id}/versions")
        
        # List versions
        response = session.get(f"{BASE_URL}/api/worlds/{world_id}/versions")
        assert response.status_code == 200, f"List versions failed: {response.text}"
        data = response.json()
        assert "versions" in data
        print(f"✓ Found {len(data['versions'])} versions for world")
    
    def test_restore_version(self, auth_session_with_world):
        """Test restoring a world to a previous version"""
        session, world_id = auth_session_with_world
        
        # Create a version
        session.post(f"{BASE_URL}/api/worlds/{world_id}/versions")
        
        # Get versions
        versions_resp = session.get(f"{BASE_URL}/api/worlds/{world_id}/versions")
        versions = versions_resp.json()["versions"]
        
        if versions:
            version_id = versions[0]["id"]
            response = session.post(f"{BASE_URL}/api/worlds/{world_id}/versions/{version_id}/restore")
            assert response.status_code == 200, f"Restore version failed: {response.text}"
            print(f"✓ World restored to version {versions[0]['version_number']}")
        else:
            print("⚠ No versions to restore (skipped)")


class TestWorldVisibility:
    """P4: World visibility toggle tests"""
    
    @pytest.fixture
    def auth_session_with_world(self):
        """Create authenticated session and get a world ID"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        # Get existing worlds
        worlds_resp = session.get(f"{BASE_URL}/api/worlds")
        worlds = worlds_resp.json()
        
        if worlds:
            world_id = worlds[0]["id"]
        else:
            create_resp = session.post(f"{BASE_URL}/api/worlds", json={
                "name": f"Test World {uuid.uuid4().hex[:6]}",
                "map_width": 32,
                "map_height": 32
            })
            world_id = create_resp.json()["id"]
        
        return session, world_id
    
    def test_toggle_visibility_public(self, auth_session_with_world):
        """Test setting world to public"""
        session, world_id = auth_session_with_world
        response = session.put(f"{BASE_URL}/api/worlds/{world_id}/visibility?is_public=true")
        assert response.status_code == 200, f"Set public failed: {response.text}"
        data = response.json()
        assert data["is_public"] == True
        print(f"✓ World set to public")
    
    def test_toggle_visibility_private(self, auth_session_with_world):
        """Test setting world to private"""
        session, world_id = auth_session_with_world
        response = session.put(f"{BASE_URL}/api/worlds/{world_id}/visibility?is_public=false")
        assert response.status_code == 200, f"Set private failed: {response.text}"
        data = response.json()
        assert data["is_public"] == False
        print(f"✓ World set to private")
    
    def test_visibility_requires_auth(self):
        """Test visibility toggle requires authentication"""
        # Get a world ID first
        worlds_resp = requests.get(f"{BASE_URL}/api/worlds")
        worlds = worlds_resp.json()
        if worlds:
            world_id = worlds[0]["id"]
            response = requests.put(f"{BASE_URL}/api/worlds/{world_id}/visibility?is_public=true")
            assert response.status_code == 401
            print("✓ Visibility toggle correctly requires auth")


class TestReviews:
    """P4: Reviews endpoint tests"""
    
    @pytest.fixture
    def auth_session_with_gallery(self):
        """Create authenticated session and get/create a gallery entry"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        # Get gallery entries
        gallery_resp = session.get(f"{BASE_URL}/api/gallery")
        assert gallery_resp.status_code == 200
        entries = gallery_resp.json().get("entries", [])
        
        if entries:
            gallery_id = entries[0]["id"]
        else:
            # Need to publish a world first
            worlds_resp = session.get(f"{BASE_URL}/api/worlds")
            worlds = worlds_resp.json()
            
            if not worlds:
                # Create a world
                create_resp = session.post(f"{BASE_URL}/api/worlds", json={
                    "name": f"Test World {uuid.uuid4().hex[:6]}",
                    "map_width": 32,
                    "map_height": 32
                })
                world_id = create_resp.json()["id"]
            else:
                world_id = worlds[0]["id"]
            
            # Publish to gallery
            publish_resp = session.post(f"{BASE_URL}/api/gallery/publish", json={
                "world_id": world_id,
                "description": "Test world for review testing",
                "creator_name": "Test Admin",
                "tags": ["test"]
            })
            if publish_resp.status_code == 200:
                gallery_id = publish_resp.json().get("id")
            elif publish_resp.status_code == 400 and "already published" in publish_resp.text.lower():
                # World already published, get its gallery entry
                gallery_resp = session.get(f"{BASE_URL}/api/gallery")
                entries = gallery_resp.json().get("entries", [])
                gallery_id = entries[0]["id"] if entries else None
            else:
                gallery_id = None
        
        return session, gallery_id
    
    def test_get_reviews(self, auth_session_with_gallery):
        """Test getting reviews for a gallery entry"""
        session, gallery_id = auth_session_with_gallery
        if not gallery_id:
            pytest.skip("No gallery entry available")
        
        response = session.get(f"{BASE_URL}/api/reviews/{gallery_id}")
        assert response.status_code == 200, f"Get reviews failed: {response.text}"
        data = response.json()
        assert "reviews" in data
        print(f"✓ Found {len(data['reviews'])} reviews for gallery entry")
    
    def test_create_review(self, auth_session_with_gallery):
        """Test creating a review"""
        session, gallery_id = auth_session_with_gallery
        if not gallery_id:
            pytest.skip("No gallery entry available")
        
        # Register a new user to create review (admin may have already reviewed)
        unique_email = f"reviewer_{uuid.uuid4().hex[:8]}@test.com"
        new_session = requests.Session()
        reg_resp = new_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Test Reviewer"
        })
        
        if reg_resp.status_code == 200:
            response = new_session.post(f"{BASE_URL}/api/reviews", json={
                "gallery_id": gallery_id,
                "rating": 5,
                "comment": f"Great world! Tested at {datetime.now().isoformat()}"
            })
            assert response.status_code == 200, f"Create review failed: {response.text}"
            print(f"✓ Review created successfully")
        else:
            print(f"⚠ Could not create new user for review test")
    
    def test_create_review_requires_auth(self, auth_session_with_gallery):
        """Test creating review requires authentication"""
        session, gallery_id = auth_session_with_gallery
        if not gallery_id:
            pytest.skip("No gallery entry available")
        
        response = requests.post(f"{BASE_URL}/api/reviews", json={
            "gallery_id": gallery_id,
            "rating": 5,
            "comment": "Should fail"
        })
        assert response.status_code == 401
        print("✓ Review creation correctly requires auth")


class TestExistingFeatures:
    """Verify existing MVP/P2/P3 features still work"""
    
    def test_worlds_crud(self):
        """Test basic world CRUD operations"""
        session = requests.Session()
        
        # List worlds
        response = session.get(f"{BASE_URL}/api/worlds")
        assert response.status_code == 200
        print(f"✓ List worlds: {len(response.json())} worlds")
        
        # Create world
        create_resp = session.post(f"{BASE_URL}/api/worlds", json={
            "name": f"P4 Test World {uuid.uuid4().hex[:6]}",
            "map_width": 32,
            "map_height": 32
        })
        assert create_resp.status_code == 200
        world_id = create_resp.json()["id"]
        print(f"✓ Create world: {world_id}")
        
        # Get world
        get_resp = session.get(f"{BASE_URL}/api/worlds/{world_id}")
        assert get_resp.status_code == 200
        print(f"✓ Get world: {get_resp.json()['name']}")
        
        # Delete world
        del_resp = session.delete(f"{BASE_URL}/api/worlds/{world_id}")
        assert del_resp.status_code == 200
        print(f"✓ Delete world: {world_id}")
    
    def test_templates_endpoint(self):
        """Test templates endpoint"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        templates = response.json().get("templates", [])
        assert len(templates) >= 5
        print(f"✓ Templates: {len(templates)} available")
    
    def test_gallery_endpoint(self):
        """Test gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        print(f"✓ Gallery: {len(response.json().get('entries', []))} entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
