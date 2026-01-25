"""Tests for response module."""

import json

from omnifocus_mcp.mcp_tools.response import build_batch_summary


class TestBuildBatchSummary:
    """Tests for build_batch_summary function."""

    def test_empty_results(self):
        """Test with empty results list."""
        summary = build_batch_summary([])
        assert summary == {
            "total": 0,
            "success": 0,
            "failed": 0,
            "results": [],
        }

    def test_all_success(self):
        """Test with all successful results."""
        results = [
            {"index": 0, "success": True, "message": "Done"},
            {"index": 1, "success": True, "message": "Done"},
        ]
        summary = build_batch_summary(results)
        assert summary["total"] == 2
        assert summary["success"] == 2
        assert summary["failed"] == 0
        assert summary["results"] == results

    def test_all_failure(self):
        """Test with all failed results."""
        results = [
            {"index": 0, "success": False, "error": "Failed"},
            {"index": 1, "success": False, "error": "Failed"},
        ]
        summary = build_batch_summary(results)
        assert summary["total"] == 2
        assert summary["success"] == 0
        assert summary["failed"] == 2

    def test_mixed_results(self):
        """Test with mixed success and failure."""
        results = [
            {"index": 0, "success": True, "message": "Done"},
            {"index": 1, "success": False, "error": "Failed"},
            {"index": 2, "success": True, "message": "Done"},
        ]
        summary = build_batch_summary(results)
        assert summary["total"] == 3
        assert summary["success"] == 2
        assert summary["failed"] == 1

    def test_custom_total(self):
        """Test with custom total parameter."""
        results = [
            {"index": 0, "success": True},
            {"index": 1, "success": True},
        ]
        # Explicitly set total to a different value
        summary = build_batch_summary(results, total=5)
        assert summary["total"] == 5
        assert summary["success"] == 2
        assert summary["failed"] == 3  # 5 - 2 = 3

    def test_results_without_success_field(self):
        """Test that results without success field count as failures."""
        results = [
            {"index": 0},  # No success field
            {"index": 1, "success": True},
        ]
        summary = build_batch_summary(results)
        assert summary["success"] == 1
        assert summary["failed"] == 1

    def test_json_serializable(self):
        """Test that the result is JSON serializable."""
        results = [
            {"index": 0, "success": True, "message": "Task added"},
        ]
        summary = build_batch_summary(results)
        # Should not raise
        json_str = json.dumps(summary)
        assert isinstance(json_str, str)
        # Should round-trip correctly
        parsed = json.loads(json_str)
        assert parsed == summary
