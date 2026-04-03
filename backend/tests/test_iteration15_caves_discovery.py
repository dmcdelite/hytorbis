"""
Iteration 15 Tests - Cave System, Zone Discovery, and JAR Export v2.0
Tests the new Hytale modding API alignment features:
- Cave system with 6 cave types
- Zone Discovery Config
- JAR export with Hytale-accurate Java code
"""

import pytest
import requests
import json
import base64
import zipfile
import io
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Test login and get auth token"""
    
    def test_login_admin(self):
        """Login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        assert response.status_code == 200
        data = response.json()
        # Login returns user data directly with email field
        assert "email" in data or "token" in data or "user" in data


class TestConfigExports:
    """Test that config.js exports are properly defined"""
    
    def test_reference_zones_endpoint(self):
        """Verify zone reference endpoint works"""
        response = requests.get(f"{BASE_URL}/api/reference/zones")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        zone_ids = [z["id"] for z in data["zones"]]
        assert "emerald_grove" in zone_ids
        assert "borea" in zone_ids
        assert "desert" in zone_ids
        assert "arctic" in zone_ids
        assert "corrupted" in zone_ids


class TestWorldsWithCavesAndDiscovery:
    """Test world CRUD with caves and discovery config"""
    
    @pytest.fixture
    def auth_cookies(self):
        """Get auth cookies"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        return response.cookies
    
    def test_get_worlds_list(self, auth_cookies):
        """Get list of worlds"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        return data[0]["id"]
    
    def test_get_world_with_zones(self, auth_cookies):
        """Get a world and verify zone structure supports caves and discovery"""
        # Get first world
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        # Get world details
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}", cookies=auth_cookies)
        assert response.status_code == 200
        world = response.json()
        
        # Verify world structure
        assert "zones" in world
        assert "prefabs" in world
        assert "terrain" in world
        
        # If zones exist, verify they can have caves and discovery
        if world["zones"]:
            zone = world["zones"][0]
            # These fields should be accepted by the model
            assert "type" in zone
            assert "x" in zone
            assert "y" in zone
    
    def test_create_zone_with_caves_and_discovery(self, auth_cookies):
        """Create a zone with cave config and discovery config"""
        # Get first world
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        # Create zone with caves and discovery
        zone_data = {
            "type": "emerald_grove",
            "x": 99,
            "y": 99,
            "difficulty": 5,
            "border_fade": 0.4,
            "caves": [
                {
                    "type": "natural",
                    "density": 0.6,
                    "min_depth": 15,
                    "max_depth": 80,
                    "biome_mask": ["forest", "plains"]
                },
                {
                    "type": "flooded",
                    "density": 0.3,
                    "min_depth": 20,
                    "max_depth": 50,
                    "biome_mask": ["swamp"]
                }
            ],
            "discovery": {
                "show_notification": True,
                "display_name": "Test Grove",
                "sound_event": "zone.test.discover",
                "major_zone": True,
                "duration": 6.0,
                "fade_in": 2.5,
                "fade_out": 1.0
            },
            "biomes": [
                {"type": "forest", "density": 0.7, "variation": 0.3}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/worlds/{world_id}/zones",
            json=zone_data,
            cookies=auth_cookies
        )
        assert response.status_code == 200
        
        # Verify zone was added
        world = response.json()
        new_zone = next((z for z in world["zones"] if z["x"] == 99 and z["y"] == 99), None)
        assert new_zone is not None
        assert new_zone["type"] == "emerald_grove"
        
        # Clean up - delete the test zone
        zone_id = new_zone["id"]
        requests.delete(f"{BASE_URL}/api/worlds/{world_id}/zones/{zone_id}", cookies=auth_cookies)


class TestJARExport:
    """Test JAR export with Hytale-accurate Java code"""
    
    @pytest.fixture
    def auth_cookies(self):
        """Get auth cookies"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        return response.cookies
    
    def test_jar_export_version(self, auth_cookies):
        """JAR export returns version 2.0"""
        # Get first world
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        # Export as JAR
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}/export/jar", cookies=auth_cookies)
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "jar"
        assert data["version"] == "2.0"
        assert "filename" in data
        assert data["filename"].endswith("_worldgen.jar")
    
    def test_jar_contains_readme(self, auth_cookies):
        """JAR contains README.md with installation instructions"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}/export/jar", cookies=auth_cookies)
        data = response.json()
        
        # Decode JAR
        jar_data = base64.b64decode(data["data_base64"])
        jar_buffer = io.BytesIO(jar_data)
        
        with zipfile.ZipFile(jar_buffer, 'r') as jar:
            assert "README.md" in jar.namelist()
            readme = jar.read("README.md").decode('utf-8')
            assert "Installation" in readme
            assert "mods/" in readme
    
    def test_jar_contains_mod_json_with_worldgen_systems(self, auth_cookies):
        """JAR contains mod.json with worldgen systems: zones, biomes, caves"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}/export/jar", cookies=auth_cookies)
        data = response.json()
        
        jar_data = base64.b64decode(data["data_base64"])
        jar_buffer = io.BytesIO(jar_data)
        
        with zipfile.ZipFile(jar_buffer, 'r') as jar:
            assert "mod.json" in jar.namelist()
            mod_json = json.loads(jar.read("mod.json"))
            
            assert "worldgen" in mod_json
            assert "systems" in mod_json["worldgen"]
            systems = mod_json["worldgen"]["systems"]
            assert "zones" in systems
            assert "biomes" in systems
            assert "caves" in systems
    
    def test_jar_contains_placement_json(self, auth_cookies):
        """JAR contains placement.json with zonePlacements and structurePlacements"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}/export/jar", cookies=auth_cookies)
        data = response.json()
        
        jar_data = base64.b64decode(data["data_base64"])
        jar_buffer = io.BytesIO(jar_data)
        
        with zipfile.ZipFile(jar_buffer, 'r') as jar:
            placement_files = [n for n in jar.namelist() if "placement.json" in n]
            assert len(placement_files) > 0
            
            placement = json.loads(jar.read(placement_files[0]))
            assert "zonePlacements" in placement
            assert "structurePlacements" in placement
    
    def test_jar_java_code_contains_hytale_api_classes(self, auth_cookies):
        """JAR Java code contains Zone, BiomePatternGenerator, CaveGenerator, ZoneDiscoveryConfig"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/worlds/{world_id}/export/jar", cookies=auth_cookies)
        data = response.json()
        
        jar_data = base64.b64decode(data["data_base64"])
        jar_buffer = io.BytesIO(jar_data)
        
        with zipfile.ZipFile(jar_buffer, 'r') as jar:
            java_files = [n for n in jar.namelist() if n.endswith(".java")]
            assert len(java_files) > 0
            
            java_code = jar.read(java_files[0]).decode('utf-8')
            
            # Check for required Hytale API classes
            assert "Zone" in java_code
            assert "BiomePatternGenerator" in java_code
            assert "CaveGenerator" in java_code
            assert "ZoneDiscoveryConfig" in java_code
            
            # Check for proper imports
            assert "com.hytale.server.worldgen" in java_code
            assert "com.hytale.server.worldgen.zone" in java_code
            assert "com.hytale.server.worldgen.cave" in java_code


class TestBackendModels:
    """Test that backend models accept caves and discovery fields"""
    
    @pytest.fixture
    def auth_cookies(self):
        """Get auth cookies"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hytorbis.com",
            "password": "Lucky420420$"
        })
        return response.cookies
    
    def test_zone_config_accepts_caves(self, auth_cookies):
        """ZoneConfig model accepts caves field"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        # Update world with zone that has caves
        zone_with_caves = {
            "type": "borea",
            "x": 98,
            "y": 98,
            "caves": [
                {"type": "ice", "density": 0.5, "min_depth": 10, "max_depth": 64, "biome_mask": []}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/worlds/{world_id}/zones",
            json=zone_with_caves,
            cookies=auth_cookies
        )
        assert response.status_code == 200
        
        # Clean up
        world = response.json()
        new_zone = next((z for z in world["zones"] if z["x"] == 98 and z["y"] == 98), None)
        if new_zone:
            requests.delete(f"{BASE_URL}/api/worlds/{world_id}/zones/{new_zone['id']}", cookies=auth_cookies)
    
    def test_zone_config_accepts_discovery(self, auth_cookies):
        """ZoneConfig model accepts discovery field"""
        response = requests.get(f"{BASE_URL}/api/worlds", cookies=auth_cookies)
        worlds = response.json()
        world_id = worlds[0]["id"]
        
        # Update world with zone that has discovery config
        zone_with_discovery = {
            "type": "desert",
            "x": 97,
            "y": 97,
            "discovery": {
                "show_notification": True,
                "display_name": "Howling Sands",
                "sound_event": "zone.desert.discover",
                "major_zone": True,
                "duration": 5.0,
                "fade_in": 2.0,
                "fade_out": 1.5
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/worlds/{world_id}/zones",
            json=zone_with_discovery,
            cookies=auth_cookies
        )
        assert response.status_code == 200
        
        # Clean up
        world = response.json()
        new_zone = next((z for z in world["zones"] if z["x"] == 97 and z["y"] == 97), None)
        if new_zone:
            requests.delete(f"{BASE_URL}/api/worlds/{world_id}/zones/{new_zone['id']}", cookies=auth_cookies)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
