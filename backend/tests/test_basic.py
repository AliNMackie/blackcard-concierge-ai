def test_imports():
    from app.models import User
    from app.services.sovereign_scheduler import sovereign_healer
    assert User is not None
    assert sovereign_healer is not None
