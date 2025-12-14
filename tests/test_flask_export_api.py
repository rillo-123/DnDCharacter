"""
Tests for Flask backend export API endpoint
Tests the /api/export POST endpoint and /api/exports GET endpoint
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Import Flask app
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend import app, EXPORT_DIR


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def cleanup_exports():
    """Clean up export files after tests"""
    yield
    # Clean up any test exports
    for file_path in EXPORT_DIR.glob('test_*.json'):
        try:
            file_path.unlink()
        except:
            pass


class TestExportEndpoint:
    """Tests for POST /api/export endpoint"""
    
    def test_export_success(self, client, cleanup_exports):
        """Test successful character export"""
        char_data = {
            'name': 'Enwer',
            'class': 'Cleric',
            'level': 9,
            'abilities': {'strength': 16, 'dexterity': 10}
        }
        
        response = client.post('/api/export', json={
            'filename': 'test_enwer.json',
            'content': char_data
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['filename'] == 'test_enwer.json'
        assert 'path' in data
        assert data['size'] > 0
    
    def test_export_file_created(self, client, cleanup_exports):
        """Test that exported file actually exists on disk"""
        char_data = {'name': 'Enwer', 'level': 9}
        
        response = client.post('/api/export', json={
            'filename': 'test_verify_file.json',
            'content': char_data
        })
        
        assert response.status_code == 200
        
        # Verify file exists
        file_path = EXPORT_DIR / 'test_verify_file.json'
        assert file_path.exists()
        
        # Verify content
        with open(file_path) as f:
            saved_data = json.load(f)
        assert saved_data == char_data
    
    def test_export_no_json_data(self, client):
        """Test export with no JSON data"""
        response = client.post('/api/export', data='')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No JSON' in data['error']
    
    def test_export_missing_filename(self, client):
        """Test export with missing filename"""
        response = client.post('/api/export', json={
            'content': {'name': 'Enwer'}
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'filename' in data['error']
    
    def test_export_missing_content(self, client):
        """Test export with missing content"""
        response = client.post('/api/export', json={
            'filename': 'test.json'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'content' in data['error']
    
    def test_export_filename_sanitization(self, client, cleanup_exports):
        """Test that path traversal is prevented"""
        char_data = {'name': 'Enwer'}
        
        # Try to use path traversal
        response = client.post('/api/export', json={
            'filename': '../../../etc/passwd',
            'content': char_data
        })
        
        assert response.status_code == 200
        data = response.get_json()
        # Should be sanitized to just the filename
        assert data['filename'] == 'passwd'
        assert '..' not in data['path']
    
    def test_export_json_formatting(self, client, cleanup_exports):
        """Test that exported JSON is properly formatted"""
        char_data = {
            'name': 'Enwer',
            'class': 'Cleric',
            'abilities': {'str': 16, 'dex': 10, 'con': 14}
        }
        
        response = client.post('/api/export', json={
            'filename': 'test_format.json',
            'content': char_data
        })
        
        assert response.status_code == 200
        
        # Read and verify formatting
        file_path = EXPORT_DIR / 'test_format.json'
        content = file_path.read_text()
        
        # Should have indentation (pretty-printed)
        assert '\n' in content
        assert '  ' in content or '\t' in content
        
        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed == char_data
    
    def test_export_complex_character(self, client, cleanup_exports):
        """Test exporting a complex character with many fields"""
        char_data = {
            'identity': {
                'name': 'Enwer',
                'class': 'Cleric',
                'level': 9,
                'race': 'Half-Orc'
            },
            'abilities': {
                'strength': 16,
                'dexterity': 10,
                'constitution': 14,
                'intelligence': 12,
                'wisdom': 15,
                'charisma': 8
            },
            'skills': {
                'acrobatics': False,
                'animal_handling': True,
                'arcana': False
            },
            'spells': {
                'prepared': ['Cure Wounds', 'Detect Magic'],
                'slots': {'1st': {'used': 2, 'total': 3}}
            }
        }
        
        response = client.post('/api/export', json={
            'filename': 'test_complex_char.json',
            'content': char_data
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify saved file
        file_path = EXPORT_DIR / 'test_complex_char.json'
        with open(file_path) as f:
            saved = json.load(f)
        assert saved == char_data
    
    def test_export_unicode_content(self, client, cleanup_exports):
        """Test exporting character with unicode characters"""
        char_data = {
            'name': 'Énwér',
            'description': 'Half-Orc with ñ and ü characters',
            'notes': '测试中文 العربية'
        }
        
        response = client.post('/api/export', json={
            'filename': 'test_unicode.json',
            'content': char_data
        })
        
        assert response.status_code == 200
        
        # Verify unicode is preserved
        file_path = EXPORT_DIR / 'test_unicode.json'
        with open(file_path, encoding='utf-8') as f:
            saved = json.load(f)
        assert saved == char_data


class TestListExportsEndpoint:
    """Tests for GET /api/exports endpoint"""
    
    def test_list_exports_empty(self, client, cleanup_exports):
        """Test listing exports when directory is empty/clean"""
        # Clean directory
        for f in EXPORT_DIR.glob('*.json'):
            try:
                f.unlink()
            except:
                pass
        
        response = client.get('/api/exports')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['exports'] == []
    
    def test_list_exports_with_files(self, client, cleanup_exports):
        """Test listing exports with multiple files"""
        # Create test files
        test_files = [
            ('test_file1.json', {'name': 'Char1'}),
            ('test_file2.json', {'name': 'Char2'}),
            ('test_file3.json', {'name': 'Char3'})
        ]
        
        for filename, content in test_files:
            file_path = EXPORT_DIR / filename
            with open(file_path, 'w') as f:
                json.dump(content, f)
        
        response = client.get('/api/exports')
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert data['count'] >= 3
        assert isinstance(data['exports'], list)
        
        # Check that our test files are in the list
        filenames = [exp['filename'] for exp in data['exports']]
        assert 'test_file1.json' in filenames
        assert 'test_file2.json' in filenames
        assert 'test_file3.json' in filenames
    
    def test_list_exports_includes_metadata(self, client, cleanup_exports):
        """Test that list includes file metadata"""
        file_path = EXPORT_DIR / 'test_metadata.json'
        with open(file_path, 'w') as f:
            json.dump({'test': 'data'}, f)
        
        response = client.get('/api/exports')
        data = response.get_json()
        
        exports = data['exports']
        assert len(exports) > 0
        
        # Check metadata fields
        test_export = next((e for e in exports if e['filename'] == 'test_metadata.json'), None)
        assert test_export is not None
        assert 'filename' in test_export
        assert 'size' in test_export
        assert 'modified' in test_export
        assert test_export['size'] > 0
    
    def test_list_exports_sorted_by_date(self, client, cleanup_exports):
        """Test that exports are sorted by modification time (most recent first)"""
        import time
        
        # Create files with slight delays to ensure different mtimes
        file1 = EXPORT_DIR / 'test_first.json'
        with open(file1, 'w') as f:
            json.dump({'order': 1}, f)
        time.sleep(0.1)
        
        file2 = EXPORT_DIR / 'test_second.json'
        with open(file2, 'w') as f:
            json.dump({'order': 2}, f)
        
        response = client.get('/api/exports')
        data = response.get_json()
        exports = data['exports']
        
        # Most recent should be first
        assert exports[0]['filename'] == 'test_second.json'


class TestExportIntegration:
    """Integration tests for export workflow"""
    
    def test_export_then_list(self, client, cleanup_exports):
        """Test exporting a character and then listing it"""
        char_data = {
            'name': 'Integration Test',
            'level': 5,
            'class': 'Fighter'
        }
        
        # Export
        export_response = client.post('/api/export', json={
            'filename': 'test_integration.json',
            'content': char_data
        })
        assert export_response.status_code == 200
        
        # List
        list_response = client.get('/api/exports')
        assert list_response.status_code == 200
        data = list_response.get_json()
        
        # Find our export in the list
        exports = data['exports']
        found = any(e['filename'] == 'test_integration.json' for e in exports)
        assert found is True
    
    def test_export_overwrite_existing(self, client, cleanup_exports):
        """Test that exporting to same filename overwrites previous version"""
        char_v1 = {'name': 'Enwer', 'level': 5}
        char_v2 = {'name': 'Enwer', 'level': 9}
        
        # Export v1
        response1 = client.post('/api/export', json={
            'filename': 'test_overwrite.json',
            'content': char_v1
        })
        assert response1.status_code == 200
        size1 = response1.get_json()['size']
        
        # Export v2
        response2 = client.post('/api/export', json={
            'filename': 'test_overwrite.json',
            'content': char_v2
        })
        assert response2.status_code == 200
        size2 = response2.get_json()['size']
        
        # File should contain v2
        file_path = EXPORT_DIR / 'test_overwrite.json'
        with open(file_path) as f:
            saved = json.load(f)
        assert saved['level'] == 9
        assert saved == char_v2
    
    def test_multiple_exports_same_session(self, client, cleanup_exports):
        """Test exporting multiple characters in sequence"""
        chars = [
            {'name': 'Enwer', 'class': 'Cleric'},
            {'name': 'Baldrick', 'class': 'Wizard'},
            {'name': 'Rilla', 'class': 'Rogue'}
        ]
        
        for i, char in enumerate(chars):
            response = client.post('/api/export', json={
                'filename': f'test_char_{i}.json',
                'content': char
            })
            assert response.status_code == 200
        
        # Verify all are listed
        list_response = client.get('/api/exports')
        data = list_response.get_json()
        filenames = [e['filename'] for e in data['exports']]
        
        for i in range(len(chars)):
            assert f'test_char_{i}.json' in filenames
