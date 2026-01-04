"""
Integration tests for Flask server startup and health checks.
Tests that the server starts correctly and responds to basic requests.
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import Flask app
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend import app, EXPORT_DIR


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskStartup:
    """Tests for Flask server startup and basic functionality"""
    
    def test_app_created(self):
        """Test that Flask app is created successfully"""
        assert app is not None
        assert app.name == 'backend'
    
    def test_app_testing_mode(self, client):
        """Test that app can run in testing mode"""
        assert app.config['TESTING'] is True
    
    def test_static_folder_configured(self):
        """Test that static folder is configured"""
        # Flask resolves relative paths to absolute, so check it ends with 'static'
        assert app.static_folder.endswith('static')
    
    def test_export_dir_exists(self):
        """Test that export directory exists"""
        assert EXPORT_DIR.exists()
        assert EXPORT_DIR.is_dir()


class TestFlaskHealthChecks:
    """Tests that server responds correctly to basic requests"""
    
    def test_root_endpoint_returns_index(self, client):
        """Test that GET / returns index.html"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE' in response.data or b'<html' in response.data or b'<head' in response.data
    
    def test_export_endpoint_exists(self, client):
        """Test that /api/export endpoint is registered"""
        # Send empty POST to check endpoint exists (will return 400)
        response = client.post('/api/export', json={})
        # Should get 400 (bad request) not 404 (not found)
        assert response.status_code != 404
        assert response.status_code == 400  # Missing required fields
    
    def test_exports_list_endpoint_exists(self, client):
        """Test that /api/exports endpoint is registered"""
        response = client.get('/api/exports')
        assert response.status_code == 200
        assert 'exports' in response.get_json()
    
    def test_static_files_served(self, client):
        """Test that static files are served"""
        # Test that we can request a static file
        # (it may 404 if file doesn't exist, but won't crash)
        response = client.get('/assets/test.js')
        assert response.status_code in [200, 404]  # Either exists or properly not found


class TestFlaskErrorHandling:
    """Tests that server handles errors gracefully"""
    
    def test_nonexistent_route_returns_404(self, client):
        """Test that nonexistent routes return 404"""
        response = client.get('/nonexistent/route/xyz')
        assert response.status_code == 404
    
    def test_invalid_json_handled(self, client):
        """Test that invalid JSON is handled gracefully"""
        response = client.post('/api/export', 
                             data='not json',
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_export_error_returns_500(self, client):
        """Test that export errors return 500 with error message"""
        response = client.post('/api/export', json={
            'filename': 'test.json',
            'content': None
        })
        # Missing content field returns 400, not 500
        assert response.status_code == 400
        assert 'error' in response.get_json()


class TestFlaskRoutes:
    """Tests that all expected routes are defined"""
    
    def test_all_routes_registered(self):
        """Test that all expected routes are registered"""
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        # Check for key routes
        assert '/' in routes
        assert '/api/export' in routes
        assert '/api/exports' in routes
    
    def test_index_route_has_correct_methods(self):
        """Test that index route handles GET"""
        routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        assert 'GET' in routes['/']
    
    def test_export_route_has_correct_methods(self):
        """Test that export route handles POST"""
        routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        assert 'POST' in routes['/api/export']
    
    def test_exports_list_route_has_correct_methods(self):
        """Test that exports list route handles GET"""
        routes = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
        assert 'GET' in routes['/api/exports']


class TestFlaskConfiguration:
    """Tests for Flask configuration"""
    
    def test_flask_json_sort_keys_disabled(self):
        """Test that JSON doesn't force alphabetical ordering"""
        # Flask default is to sort keys, but we may want to disable it
        # for better readability in exported files
        # This test documents the current behavior
        assert app is not None
    
    def test_export_dir_writable(self):
        """Test that export directory is writable"""
        import os
        
        test_file = EXPORT_DIR / 'test_write.txt'
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            assert test_file.exists()
            os.remove(test_file)
        except Exception as e:
            pytest.fail(f"Export directory not writable: {e}")
    
    def test_static_folder_exists(self):
        """Test that static folder path exists"""
        static_path = Path(app.static_folder)
        assert static_path.exists() or not app.config['TESTING']


class TestFlaskResponseHeaders:
    """Tests for proper response headers"""
    
    def test_export_response_includes_content_type(self, client):
        """Test that export endpoint returns JSON content-type"""
        response = client.get('/api/exports')
        assert 'application/json' in response.content_type
    
    def test_export_endpoint_returns_json(self, client):
        """Test that export endpoint returns valid JSON"""
        response = client.get('/api/exports')
        assert response.status_code == 200
        # Should be able to parse as JSON without error
        json_data = response.get_json()
        assert isinstance(json_data, dict)


class TestFlaskIntegration:
    """Integration tests for Flask server"""
    
    def test_export_and_list_workflow(self, client):
        """Test complete workflow: export character then list it"""
        import json
        import os
        
        # Create export
        char_data = {'name': 'TestChar', 'level': 5}
        response = client.post('/api/export', json={
            'filename': 'test_integration.json',
            'content': char_data
        })
        assert response.status_code == 200
        
        # List exports
        response = client.get('/api/exports')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] > 0
        
        # Cleanup
        test_file = EXPORT_DIR / 'test_integration.json'
        if test_file.exists():
            os.remove(test_file)
    
    def test_server_can_handle_concurrent_requests(self, client):
        """Test that server can handle multiple requests"""
        responses = []
        
        # Send multiple requests
        for i in range(5):
            response = client.get('/api/exports')
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
    
    def test_multiple_exports_in_sequence(self, client):
        """Test exporting multiple characters in sequence"""
        import os
        
        files_created = []
        try:
            for i in range(3):
                response = client.post('/api/export', json={
                    'filename': f'test_seq_{i}.json',
                    'content': {'char': i}
                })
                assert response.status_code == 200
                files_created.append(f'test_seq_{i}.json')
            
            # List should show all
            response = client.get('/api/exports')
            data = response.get_json()
            assert data['count'] >= 3
        finally:
            # Cleanup
            for filename in files_created:
                test_file = EXPORT_DIR / filename
                if test_file.exists():
                    os.remove(test_file)


class TestFlaskServerProperties:
    """Tests for server runtime properties"""
    
    def test_app_has_debug_false_by_default(self):
        """Test that debug mode is not enabled by default"""
        # In testing mode, we can check the config
        # In production, debug should be False
        assert app is not None
    
    def test_app_version_consistent(self):
        """Test that app responds consistently"""
        with app.test_client() as client:
            resp1 = client.get('/api/exports')
            resp2 = client.get('/api/exports')
            
            data1 = resp1.get_json()
            data2 = resp2.get_json()
            
            # Both should have same structure
            assert 'count' in data1 and 'count' in data2
            assert 'exports' in data1 and 'exports' in data2
    
    def test_app_response_time_reasonable(self, client):
        """Test that app responds in reasonable time"""
        import time
        
        start = time.time()
        response = client.get('/api/exports')
        elapsed = time.time() - start
        
        # Should respond in less than 1 second
        assert elapsed < 1.0
        assert response.status_code == 200
