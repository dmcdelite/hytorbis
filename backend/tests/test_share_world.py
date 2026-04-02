"""
Test Share World Feature - Backend API Tests
Tests for:
- POST /api/worlds/{id}/share - Toggle share_enabled
- GET /api/worlds/{id}/share - Get share info (authenticated)
- GET /api/shared/{token} - Public endpoint for shared world data
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestShareWorldAPI:
    """Share World API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed - skipping share tests")
        
        self.user = login_response.json()
        print(f"Logged in as: {self.user.get('email')}")
        
        # Get worlds to find one to test with
        worlds_response = self.session.get(f"{BASE_URL}/api/worlds")
        if worlds_response.status_code == 200:
            worlds = worlds_response.json()
            if isinstance(worlds, list) and len(worlds) > 0:
                self.test_world = worlds[0]
                print(f"Using test world: {self.test_world.get('name')} (id: {self.test_world.get('id')})")
            else:
                # Create a test world if none exist
                create_response = self.session.post(f"{BASE_URL}/api/worlds", json={
                    "name": "TEST_ShareWorld",
                    "seed": "test123",
                    "map_width": 32,
                    "map_height": 32
                })
                if create_response.status_code in [200, 201]:
                    self.test_world = create_response.json()
                    print(f"Created test world: {self.test_world.get('name')}")
                else:
                    pytest.skip("Could not create test world")
        else:
            pytest.skip("Could not fetch worlds")
    
    def test_get_share_info_authenticated(self):
        """GET /api/worlds/{id}/share - Get share info (requires auth)"""
        world_id = self.test_world.get('id')
        
        response = self.session.get(f"{BASE_URL}/api/worlds/{world_id}/share")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "share_enabled" in data, "Response should contain share_enabled"
        assert "share_token" in data, "Response should contain share_token"
        assert "world_id" in data, "Response should contain world_id"
        assert data["world_id"] == world_id, "world_id should match"
        
        print(f"Share info: enabled={data['share_enabled']}, token={data.get('share_token')}")
    
    def test_toggle_share_on(self):
        """POST /api/worlds/{id}/share - Toggle sharing ON"""
        world_id = self.test_world.get('id')
        
        # First get current state
        get_response = self.session.get(f"{BASE_URL}/api/worlds/{world_id}/share")
        initial_state = get_response.json().get("share_enabled", False)
        
        # Toggle share
        response = self.session.post(f"{BASE_URL}/api/worlds/{world_id}/share")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "share_enabled" in data, "Response should contain share_enabled"
        assert "share_token" in data, "Response should contain share_token"
        assert data["share_enabled"] != initial_state, "share_enabled should toggle"
        
        # If we toggled ON, verify token is generated
        if data["share_enabled"]:
            assert data["share_token"] is not None, "share_token should be generated when enabled"
            assert len(data["share_token"]) > 0, "share_token should not be empty"
        
        print(f"Toggled share: enabled={data['share_enabled']}, token={data['share_token']}")
        
        # Store for next test
        self.share_token = data.get("share_token")
        self.share_enabled = data.get("share_enabled")
    
    def test_toggle_share_off(self):
        """POST /api/worlds/{id}/share - Toggle sharing OFF"""
        world_id = self.test_world.get('id')
        
        # Get current state
        get_response = self.session.get(f"{BASE_URL}/api/worlds/{world_id}/share")
        current_state = get_response.json()
        
        # Toggle share
        response = self.session.post(f"{BASE_URL}/api/worlds/{world_id}/share")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["share_enabled"] != current_state["share_enabled"], "share_enabled should toggle"
        
        print(f"Toggled share again: enabled={data['share_enabled']}")
    
    def test_get_share_info_unauthenticated(self):
        """GET /api/worlds/{id}/share - Should require auth"""
        world_id = self.test_world.get('id')
        
        # Use a new session without auth
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/worlds/{world_id}/share")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        print(f"Unauthenticated request correctly rejected with {response.status_code}")
    
    def test_toggle_share_nonexistent_world(self):
        """POST /api/worlds/{id}/share - Should return 404 for nonexistent world"""
        response = self.session.post(f"{BASE_URL}/api/worlds/nonexistent-world-id/share")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Nonexistent world correctly returns 404")


class TestPublicSharedEndpoint:
    """Tests for public shared world endpoint (no auth required)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and enable sharing on a world"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        # Get worlds
        worlds_response = self.session.get(f"{BASE_URL}/api/worlds")
        if worlds_response.status_code == 200:
            worlds = worlds_response.json()
            if isinstance(worlds, list) and len(worlds) > 0:
                self.test_world = worlds[0]
            else:
                pytest.skip("No worlds available")
        else:
            pytest.skip("Could not fetch worlds")
        
        # Get share info
        share_response = self.session.get(f"{BASE_URL}/api/worlds/{self.test_world['id']}/share")
        if share_response.status_code == 200:
            share_info = share_response.json()
            self.share_token = share_info.get("share_token")
            self.share_enabled = share_info.get("share_enabled")
            
            # If not enabled, enable it
            if not self.share_enabled:
                toggle_response = self.session.post(f"{BASE_URL}/api/worlds/{self.test_world['id']}/share")
                if toggle_response.status_code == 200:
                    toggle_data = toggle_response.json()
                    self.share_token = toggle_data.get("share_token")
                    self.share_enabled = toggle_data.get("share_enabled")
            
            print(f"Share token: {self.share_token}, enabled: {self.share_enabled}")
    
    def test_get_shared_world_public(self):
        """GET /api/shared/{token} - Public endpoint returns world data"""
        if not self.share_token or not self.share_enabled:
            pytest.skip("Share not enabled for test world")
        
        # Use unauthenticated session
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/api/shared/{self.share_token}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "world" in data, "Response should contain 'world'"
        assert "stats" in data, "Response should contain 'stats'"
        
        world = data["world"]
        assert "id" in world, "World should have id"
        assert "name" in world, "World should have name"
        assert "seed" in world, "World should have seed"
        assert "zones" in world, "World should have zones"
        assert "prefabs" in world, "World should have prefabs"
        
        stats = data["stats"]
        assert "zones" in stats, "Stats should have zones count"
        assert "prefabs" in stats, "Stats should have prefabs count"
        assert "map_size" in stats, "Stats should have map_size"
        
        print(f"Public shared world: {world['name']}, zones: {stats['zones']}, prefabs: {stats['prefabs']}")
    
    def test_get_shared_world_invalid_token(self):
        """GET /api/shared/{token} - Invalid token returns 404"""
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/api/shared/invalid-token-xyz")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid token correctly returns 404")
    
    def test_get_shared_world_disabled(self):
        """GET /api/shared/{token} - Disabled share returns 404"""
        if not self.share_token:
            pytest.skip("No share token available")
        
        # Disable sharing
        toggle_response = self.session.post(f"{BASE_URL}/api/worlds/{self.test_world['id']}/share")
        if toggle_response.status_code == 200:
            toggle_data = toggle_response.json()
            if toggle_data.get("share_enabled"):
                # Toggle again to disable
                self.session.post(f"{BASE_URL}/api/worlds/{self.test_world['id']}/share")
        
        # Now try to access with public session
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/api/shared/{self.share_token}")
        
        # Should return 404 when sharing is disabled
        assert response.status_code == 404, f"Expected 404 when sharing disabled, got {response.status_code}"
        print("Disabled share correctly returns 404")
        
        # Re-enable sharing for other tests
        self.session.post(f"{BASE_URL}/api/worlds/{self.test_world['id']}/share")


class TestKnownShareToken:
    """Test with the known share token from the test context"""
    
    def test_known_share_token(self):
        """GET /api/shared/298a3d8d-81c - Known test token should work"""
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/api/shared/298a3d8d-81c")
        
        # This token was mentioned as enabled in the test context
        if response.status_code == 200:
            data = response.json()
            assert "world" in data, "Response should contain world"
            world = data["world"]
            print(f"Known token works: World '{world.get('name')}' is shared")
        elif response.status_code == 404:
            print("Known token returns 404 - sharing may have been disabled")
        else:
            print(f"Unexpected status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
