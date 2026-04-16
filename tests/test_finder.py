from pathlib import Path

import hallucipip
from hallucipip.finder import HallucipipFinder


def test_finder_generates_and_caches_missing_module(monkeypatch, tmp_path: Path) -> None:
    hallucipip.configure(
        model="test-model",
        api_key="test-key",
        cache_dir=str(tmp_path),
        hallucination_intensity=3,
        debug=False,
    )

    monkeypatch.setattr("hallucipip.finder._is_stdlib_or_installed", lambda _: False)
    monkeypatch.setattr("hallucipip.finder._extract_version_hint", lambda _: ">=1.0")
    monkeypatch.setattr(
        "hallucipip.finder.generate_module",
        lambda *args, **kwargs: "__version__ = '0.0.test'\nvalue = 42\n",
    )

    finder = HallucipipFinder()
    spec = finder.find_spec("synthetic_demo", None)

    assert spec is not None
    assert spec.origin is not None
    assert Path(spec.origin).exists()
    assert "value = 42" in Path(spec.origin).read_text(encoding="utf-8")
