from hallucipip.prompts import build_request_signature, build_user_prompt


def test_build_user_prompt_includes_version_hint() -> None:
    prompt = build_user_prompt("demo_lib", ">=2.0,<3", 4)

    assert "demo_lib" in prompt
    assert ">=2.0,<3" in prompt


def test_request_signature_changes_with_request_shape() -> None:
    baseline = build_request_signature(
        "demo_lib",
        model="model-a",
        version_hint=None,
        hallucination_intensity=5,
    )
    changed = build_request_signature(
        "demo_lib",
        model="model-a",
        version_hint=">=2.0",
        hallucination_intensity=5,
    )

    assert baseline != changed
