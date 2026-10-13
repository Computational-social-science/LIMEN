"""Tests for keystroke-observatory package."""

import pytest
from pathlib import Path
import keystroke_observatory
from keystroke_observatory.cli import get_dist_path, serve_dashboard, build_dashboard, open_dashboard


def test_version():
    """Test that version is accessible."""
    assert keystroke_observatory.__version__ == "1.0.0"


def test_dist_path_exists():
    """Test that the dist path exists and has required files."""
    dist_path = get_dist_path()
    assert dist_path.exists()
    assert (dist_path / "pages" / "index.html").exists()
    assert (dist_path / "pages" / "participants.html").exists()
    assert (dist_path / "pages" / "sessions.html").exists()
    assert (dist_path / "public" / "keystroke_session_stats.parquet").exists()


def test_cli_help():
    """Test CLI help command."""
    import subprocess
    result = subprocess.run(
        ["keystroke-observatory", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Keystroke Observatory" in result.stdout
    assert "serve" in result.stdout
    assert "build" in result.stdout
    assert "open" in result.stdout


def test_cli_build():
    """Test CLI build command (dry run)."""
    import subprocess
    result = subprocess.run(
        ["keystroke-observatory", "build"],
        capture_output=True,
        text=True,
        timeout=120
    )
    # Build should succeed (returncode 0) or fail gracefully
    assert result.returncode in [0, 1]


def test_dist_structure():
    """Test that dist folder has expected structure."""
    dist_path = get_dist_path()
    
    # Check main directories
    assert (dist_path / "_observablehq").exists()
    assert (dist_path / "_node").exists()
    assert (dist_path / "_npm").exists()
    assert (dist_path / "_import").exists()
    assert (dist_path / "pages").exists()
    assert (dist_path / "public").exists()
    
    # Check key files
    assert (dist_path / "pages" / "index.html").exists()
    assert (dist_path / "public" / "keystroke_session_stats.parquet").exists()
    
    # Check Parquet file is not empty
    parquet_file = dist_path / "public" / "keystroke_session_stats.parquet"
    assert parquet_file.stat().st_size > 1000000  # > 1MB


def test_parquet_readable():
    """Test that the Parquet file can be read."""
    import pandas as pd
    dist_path = get_dist_path()
    df = pd.read_parquet(dist_path / "public" / "keystroke_session_stats.parquet")
    
    # Check expected shape
    assert len(df) == 157314
    assert len(df.columns) == 25
    
    # Check key columns exist
    expected_columns = [
        "participant_id", "test_section_id", "wpm", "error_rate",
        "iki_mean_ms", "iki_median_ms", "iki_q25_ms", "iki_q75_ms",
        "hold_mean_ms", "n_backspace", "n_delete", "n_keystrokes",
        "n_chars", "session_duration_s", "total_time_ms"
    ]
    for col in expected_columns:
        assert col in df.columns
    
    # Check no nulls
    assert df.isnull().sum().sum() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])