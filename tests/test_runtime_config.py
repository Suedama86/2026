from uoa_agent.api import resolve_bind


def test_resolve_bind_prefers_platform_port(monkeypatch) -> None:
    monkeypatch.setenv("UOA_HOST", "0.0.0.0")
    monkeypatch.setenv("UOA_PORT", "8000")
    monkeypatch.setenv("PORT", "10000")

    host, port = resolve_bind()
    assert host == "0.0.0.0"
    assert port == 10000


def test_resolve_bind_falls_back_on_invalid_port(monkeypatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setenv("UOA_PORT", "invalid")

    host, port = resolve_bind()
    assert host == "0.0.0.0"
    assert port == 8000
