from app.config import Settings


def test_runwayml_api_secret_maps(monkeypatch) -> None:
    monkeypatch.setenv("RUNWAYML_API_SECRET", "rw_test_secret_123")
    s = Settings()
    assert s.runwayml_api_secret == "rw_test_secret_123"


def test_demo_manager_password_maps(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_MANAGER_PASSWORD", "hunter2")
    s = Settings()
    assert s.demo_manager_password == "hunter2"
