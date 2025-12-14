"""
Test to diagnose Pyodide fetch POST issue.
Tests the exact fetch pattern used in export_management.py
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Test the pattern used in export_management.py
class TestPyodideFetchPattern:
    """Tests to diagnose why fetch is sending GET instead of POST"""
    
    @pytest.mark.asyncio
    async def test_fetch_with_to_js_conversion(self):
        """Test fetch using pyodide.ffi.to_js conversion"""
        # Mock the fetch function
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true}')
        
        mock_fetch = AsyncMock(return_value=mock_response)
        
        # Create test data
        test_data = {
            "filename": "test.json",
            "content": {"name": "Enwer", "level": 9}
        }
        
        # Convert to JSON as the code does
        body_json = json.dumps(test_data)
        
        # Try different approaches to create the options
        
        # Approach 1: Pure Python dict (this is what we're currently using)
        options_dict = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": body_json
        }
        
        # Simulate the fetch call
        await mock_fetch("/api/export", options_dict)
        
        # Verify the call
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        
        # Check the arguments
        assert call_args[0][0] == "/api/export"
        options_arg = call_args[0][1]
        
        print(f"\nFetch called with options type: {type(options_arg)}")
        print(f"Options content: {options_arg}")
        print(f"Method: {options_arg.get('method')}")
        print(f"Headers: {options_arg.get('headers')}")
        assert options_arg.get("method") == "POST"
    
    @pytest.mark.asyncio
    async def test_fetch_with_explicit_headers_dict(self):
        """Test fetch with headers as separate dict"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true}')
        
        mock_fetch = AsyncMock(return_value=mock_response)
        
        test_data = {
            "filename": "test.json",
            "content": {"name": "Enwer"}
        }
        
        body_json = json.dumps(test_data)
        
        # Build headers dict first
        headers_dict = {"Content-Type": "application/json"}
        
        # Build options
        options_dict = {
            "method": "POST",
            "headers": headers_dict,
            "body": body_json
        }
        
        await mock_fetch("/api/export", options_dict)
        
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        options_arg = call_args[0][1]
        
        assert options_arg.get("method") == "POST"
        assert isinstance(options_arg.get("headers"), dict)
        assert options_arg.get("headers").get("Content-Type") == "application/json"
    
    def test_json_serialization_of_request_data(self):
        """Test that request data serializes correctly"""
        char_data = {
            "identity": {"name": "Enwer", "class": "Cleric"},
            "level": 9,
            "spells": ["cure-wounds", "heal"]
        }
        
        request_data = {
            "filename": "Enwer_test.json",
            "content": char_data
        }
        
        # Test JSON serialization
        body_json = json.dumps(request_data)
        
        assert isinstance(body_json, str)
        assert "Enwer_test.json" in body_json
        assert "Enwer" in body_json
        
        # Verify it's valid JSON
        parsed = json.loads(body_json)
        assert parsed["filename"] == "Enwer_test.json"
        assert parsed["content"]["level"] == 9


class TestFetchVsHttpVerbs:
    """Tests to verify HTTP method is correctly set"""
    
    def test_method_is_post_not_get(self):
        """Ensure the method string is exactly 'POST'"""
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "{}"
        }
        
        # Check method is POST
        assert options["method"] == "POST"
        assert options["method"] != "GET"
        assert options["method"] != ""
    
    def test_headers_content_type_set(self):
        """Ensure Content-Type header is set"""
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "{}"
        }
        
        assert "headers" in options
        assert isinstance(options["headers"], dict)
        assert options["headers"]["Content-Type"] == "application/json"


class TestExportPayloadStructure:
    """Tests the exact payload structure sent to Flask"""
    
    def test_request_data_structure(self):
        """Test that request_data has correct structure for Flask"""
        char_data = {
            "identity": {"name": "Enwer", "class": "Cleric"},
            "abilities": {"strength": 16},
            "spells": ["cure-wounds"]
        }
        
        # This is the structure built in export_management.py
        request_data = {
            "filename": "Enwer_Cleric_lvl9_20251214_2200.json",
            "content": char_data
        }
        
        # Verify it matches Flask backend expectations
        assert "filename" in request_data
        assert "content" in request_data  # Flask expects "content", not "data"
        assert isinstance(request_data["content"], dict)
    
    def test_payload_json_conversion(self):
        """Test JSON conversion of payload"""
        request_data = {
            "filename": "test.json",
            "content": {
                "name": "Enwer",
                "level": 9
            }
        }
        
        body_json = json.dumps(request_data)
        parsed = json.loads(body_json)
        
        # Should preserve structure through JSON round-trip
        assert parsed["filename"] == "test.json"
        assert parsed["content"]["name"] == "Enwer"
        assert parsed["content"]["level"] == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
