"""Test utilities module."""

import pytest
from omnifocus_mcp.utils import escape_applescript_string


class TestEscapeAppleScriptString:
    """Tests for escape_applescript_string function."""
    
    def test_no_special_characters(self):
        """Test string with no special characters."""
        result = escape_applescript_string("Hello World")
        assert result == "Hello World"
    
    def test_escape_quotes(self):
        """Test escaping double quotes."""
        result = escape_applescript_string('Test "quoted" text')
        assert result == 'Test \\"quoted\\" text'
    
    def test_escape_backslashes(self):
        """Test escaping backslashes."""
        result = escape_applescript_string('Test \\backslash\\')
        assert result == 'Test \\\\backslash\\\\'
    
    def test_escape_both_quotes_and_backslashes(self):
        """Test escaping both quotes and backslashes."""
        result = escape_applescript_string('Combined " and \\')
        assert result == 'Combined \\" and \\\\'
    
    def test_empty_string(self):
        """Test empty string."""
        result = escape_applescript_string("")
        assert result == ""
    
    def test_multiple_quotes(self):
        """Test multiple quotes in sequence."""
        result = escape_applescript_string('"""')
        assert result == '\\"\\"\\"'
    
    def test_multiple_backslashes(self):
        """Test multiple backslashes in sequence."""
        result = escape_applescript_string('\\\\\\')
        assert result == '\\\\\\\\\\\\'
