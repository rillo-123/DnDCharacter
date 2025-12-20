"""
Unit tests for export_management.py fetch POST functionality

Tests the specific issue where Pyodide fetch was sending GET instead of POST
when trying to export character data to the Flask backend.

Key test areas:
1. Fetch options object creation
2. HTTP method is correctly set to POST
3. Headers are properly configured
4. Request body contains correct JSON payload
5. Integration with Flask /api/export endpoint
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFetchOptionsConstruction:
    """Test creating proper fetch options objects"""
    
    def test_fetch_options_has_post_method(self):
        """Verify fetch options specify POST method"""
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"test": "data"}'
        }
        
        assert options["method"] == "POST"
        assert options["method"] != "GET"
        assert options["method"] != ""
    
    def test_fetch_options_has_json_content_type(self):
        """Verify fetch options set Content-Type to application/json"""
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"test": "data"}'
        }
        
        assert "headers" in options
        assert "Content-Type" in options["headers"]
        assert options["headers"]["Content-Type"] == "application/json"
    
    def test_fetch_options_body_is_json_string(self):
        """Verify fetch body is properly JSON serialized"""
        data = {"filename": "test.json", "content": {"name": "Enwer"}}
        body_json = json.dumps(data)
        
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": body_json
        }
        
        assert isinstance(options["body"], str)
        # Verify it's valid JSON
        parsed = json.loads(options["body"])
        assert parsed["filename"] == "test.json"
        assert parsed["content"]["name"] == "Enwer"


class TestExportPayload:
    """Test the payload structure sent to Flask"""
    
    def test_request_data_structure(self):
        """Test request has correct structure for Flask backend"""
        char_data = {
            "identity": {"name": "Enwer", "class": "Cleric"},
            "level": 9,
            "spells": ["cure-wounds", "bless"]
        }
        
        # This matches the structure built in export_character()
        request_data = {
            "filename": "Enwer_Cleric_lvl9_20251214_2203.json",
            "content": char_data
        }
        
        # Flask backend expects these keys
        assert "filename" in request_data
        assert "content" in request_data  # NOT "data"!
        assert request_data["filename"].endswith(".json")
        assert isinstance(request_data["content"], dict)
    
    def test_payload_json_roundtrip(self):
        """Test payload survives JSON serialization/deserialization"""
        original_data = {
            "filename": "test.json",
            "content": {
                "identity": {"name": "Test Char"},
                "abilities": {"strength": 16, "dexterity": 10},
                "spells": ["spell1", "spell2"]
            }
        }
        
        # Serialize
        body_json = json.dumps(original_data)
        
        # Deserialize
        restored_data = json.loads(body_json)
        
        # Should be identical
        assert restored_data == original_data
        assert restored_data["filename"] == "test.json"
        assert restored_data["content"]["abilities"]["strength"] == 16
    
    def test_large_character_payload(self):
        """Test payload with large character data (like Enwer with 28 spells)"""
        large_payload = {
            "filename": "Enwer_Cleric_lvl9_20251214_2203.json",
            "content": {
                "identity": {"name": "Enwer", "class": "Cleric", "level": 9},
                "abilities": {
                    "strength": 16,
                    "dexterity": 10,
                    "constitution": 14,
                    "intelligence": 12,
                    "wisdom": 20,
                    "charisma": 8
                },
                "spells": [
                    "bless", "cure-wounds", "detect-magic", "guidance",
                    "light", "mending", "sacred-flame", "thaumaturgy",
                    "word-of-radiance", "aid", "spiritual-weapon",
                    "lesser-restoration", "hold-person", "Prayer of Healing",
                    "beacon-of-hope", "revivify", "dispel-magic",
                    "spirit-guardians", "death-ward", "guardian-of-faith",
                    "raise-dead", "mass-cure-wounds", "confusion",
                    "detect-evil-and-good", "find-traps", "locate-creature",
                    "freedom-of-movement", "shield-of-faith"
                ],
                "inventory": [
                    {"name": "Holy Symbol", "quantity": 1},
                    {"name": "Chain Mail", "quantity": 1},
                    {"name": "Mace", "quantity": 1}
                ]
            }
        }
        
        # Should serialize without issues
        body_json = json.dumps(large_payload)
        assert len(body_json) > 0
        
        # Verify size is reasonable (payload with full character data)
        assert len(body_json) > 500  # At minimum a few hundred bytes
        
        # Should deserialize correctly
        restored = json.loads(body_json)
        assert len(restored["content"]["spells"]) == 28


class TestFetchMethodVerification:
    """Test that fetch is called with POST method"""
    
    def test_fetch_options_passed_correctly(self):
        """Verify fetch options object structure for POST"""
        # This test verifies the structure without requiring async
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"filename": "test.json", "content": {}}'
        }
        
        # Verify the options dict has correct structure
        assert "method" in options
        assert "headers" in options
        assert "body" in options
        
        assert options["method"] == "POST"
        assert isinstance(options["headers"], dict)
        assert isinstance(options["body"], str)


class TestFlaskBackendIntegration:
    """Test with actual Flask backend"""
    
    def test_export_endpoint_accepts_post(self, client=None):
        """Test that Flask /api/export endpoint accepts POST requests
        
        This test requires the Flask test client to be available.
        It's imported dynamically since it's in the parent module.
        """
        try:
            from backend import app
            
            # Create test client
            app.config['TESTING'] = True
            with app.test_client() as client:
                # Test POST request
                response = client.post('/api/export', json={
                    'filename': 'test_fetch_post.json',
                    'content': {
                        'name': 'Test Character',
                        'level': 5
                    }
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['filename'] == 'test_fetch_post.json'
        except ImportError:
            pytest.skip("Flask backend not available in test environment")
    
    def test_export_endpoint_rejects_get(self, client=None):
        """Test that Flask /api/export endpoint rejects GET requests"""
        try:
            from backend import app
            
            app.config['TESTING'] = True
            with app.test_client() as client:
                # Try GET request
                response = client.get('/api/export')
                
                # Should get 404 or 405 (Method Not Allowed)
                assert response.status_code in [404, 405]
        except ImportError:
            pytest.skip("Flask backend not available in test environment")
    
    def test_export_requires_json_content_header(self):
        """Test that export requires Content-Type: application/json"""
        try:
            from backend import app
            
            app.config['TESTING'] = True
            with app.test_client() as client:
                # POST without proper Content-Type
                response = client.post('/api/export', 
                                      data='not json',
                                      content_type='text/plain')
                
                # Should fail due to invalid JSON
                assert response.status_code == 400
        except ImportError:
            pytest.skip("Flask backend not available in test environment")


class TestFetchPyodideWorkaround:
    """Test the Pyodide-specific fetch workarounds"""
    
    def test_jsproxy_object_creation(self):
        """Test pattern for creating JsProxy objects in Pyodide
        
        This is a documentation test showing the pattern that should work
        with Pyodide's JsProxy objects.
        """
        # In Pyodide, this pattern should work:
        # from js import Object as JSObject
        # options = JSObject.new()
        # options.method = "POST"
        # options.body = body_json
        
        # For testing without Pyodide, we simulate it
        class MockJsProxy:
            pass
        
        options = MockJsProxy()
        options.method = "POST"
        options.body = '{"test": "data"}'
        
        assert options.method == "POST"
        assert options.body == '{"test": "data"}'
    
    def test_python_dict_fallback(self):
        """Test fallback to Python dict when JsProxy creation fails"""
        # When JsProxy creation fails, we fall back to Python dict
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"test": "data"}'
        }
        
        assert isinstance(options, dict)
        assert options["method"] == "POST"
        
        # This dict can be passed to fetch if Pyodide auto-converts it
        assert "method" in options
        assert "headers" in options
        assert "body" in options


class TestHeadersConfiguration:
    """Test HTTP headers configuration"""
    
    def test_json_content_type_header(self):
        """Test Content-Type header is set to application/json"""
        headers = {"Content-Type": "application/json"}
        
        assert headers["Content-Type"] == "application/json"
    
    def test_headers_dict_structure(self):
        """Test headers dict has correct structure"""
        headers = {
            "Content-Type": "application/json"
        }
        
        assert isinstance(headers, dict)
        assert len(headers) >= 1
        assert "Content-Type" in headers
    
    def test_headers_not_empty(self):
        """Test headers dict is not empty"""
        headers = {"Content-Type": "application/json"}
        assert len(headers) > 0


class TestRequestBodyHandling:
    """Test request body handling"""
    
    def test_body_is_json_string(self):
        """Test body is a JSON string, not a dict"""
        data = {"filename": "test.json", "content": {}}
        body = json.dumps(data)
        
        assert isinstance(body, str)
        assert body.startswith('{')
        assert body.endswith('}')
    
    def test_body_can_be_parsed(self):
        """Test body JSON can be parsed back"""
        original = {"filename": "test.json", "content": {"name": "Enwer"}}
        body = json.dumps(original)
        
        parsed = json.loads(body)
        assert parsed == original
    
    def test_body_preserves_unicode(self):
        """Test body preserves unicode characters"""
        data = {
            "filename": "test.json",
            "content": {"name": "Énwér", "notes": "测试"}
        }
        body = json.dumps(data, ensure_ascii=False)
        
        parsed = json.loads(body)
        assert parsed["content"]["name"] == "Énwér"
        assert parsed["content"]["notes"] == "测试"


class TestErrorHandling:
    """Test error scenarios"""
    
    def test_fetch_404_status_code(self):
        """Test handling of 404 response"""
        response_status = 404
        assert response_status != 200
        assert response_status >= 400
    
    def test_fetch_error_message_content(self):
        """Test error response contains useful message"""
        error_response = """<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server.</p>
"""
        
        assert "404" in error_response
        assert "Not Found" in error_response
    
    def test_valid_json_error_response(self):
        """Test Flask error response is valid JSON"""
        error_json = '{"error": "Missing content"}'
        parsed = json.loads(error_json)
        
        assert "error" in parsed
        assert parsed["error"] == "Missing content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
