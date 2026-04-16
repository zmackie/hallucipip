from pathlib import Path

from hallucipip import cache


def test_cache_round_trip(tmp_path: Path) -> None:
    path = cache.put("demo_module", "abc123", "value = 1\n", tmp_path)

    assert path.exists()
    assert cache.get("demo_module", "abc123", tmp_path) == path
    assert path.read_text(encoding="utf-8") == "value = 1\n"


def test_clear_returns_removed_file_count(tmp_path: Path) -> None:
    cache.put("one", "111", "x = 1\n", tmp_path)
    cache.put("two", "222", "x = 2\n", tmp_path)

    assert cache.clear(tmp_path) == 2
    assert cache.list_cached(tmp_path) == []
