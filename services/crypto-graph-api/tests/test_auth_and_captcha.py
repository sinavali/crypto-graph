import pytest
from libs.blockchain_contracts.auth_models import UserRole
from src.domain.auth_service import AuthService
from src.domain.captcha import CaptchaEngine
from src.infrastructure.sqlite_storage import SqliteGraphStorage


def test_captcha_generation_and_validation():
    engine = CaptchaEngine(secret_key="test_secret_key_123")
    cid, svg = engine.generate_challenge()
    assert len(cid) > 0
    assert "<svg" in svg
    assert "</svg>" in svg

    # Challenge is stored
    challenge = engine._challenges[cid]
    # Solve challenge using known answer
    text = challenge.question_text
    if "+" in text:
        a, b = text.split("+")
        b = b.replace("= ?", "").strip()
        ans = str(int(a.strip()) + int(b))
    elif "-" in text:
        a, b = text.split("-")
        b = b.replace("= ?", "").strip()
        ans = str(int(a.strip()) - int(b))
    elif "×" in text:
        a, b = text.split("×")
        b = b.replace("= ?", "").strip()
        ans = str(int(a.strip()) * int(b))
    else:
        ans = text.replace(" ", "")

    # Invalid answer fails
    assert engine.verify_answer("non_existent", "0") is False

    # Valid answer passes
    assert engine.verify_answer(cid, ans) is True
    # Replay attack fails (challenge consumed)
    assert engine.verify_answer(cid, ans) is False


def test_auth_service_registration_and_login():
    storage = SqliteGraphStorage(":memory:")
    auth = AuthService(storage)

    # Admin was seeded
    admin_user = storage.get_user_by_username("admin")
    assert admin_user is not None
    assert admin_user.role == UserRole.ADMIN

    # Register new user
    user = auth.register_user(
        username="trader1",
        password="SecretPassword123!",
        tenant_name="Alpha Fund",
    )
    assert user.username == "trader1"
    assert user.tenant_id.startswith("tenant-")
    assert user.role == UserRole.MEMBER

    # Duplicate username rejected
    with pytest.raises(ValueError):
        auth.register_user("trader1", "AnotherPassword!")

    # Login with valid credentials
    session = auth.authenticate("trader1", "SecretPassword123!")
    assert session.username == "trader1"
    assert session.token is not None
    assert session.is_expired is False

    # Validate session
    validated = auth.validate_session(session.token)
    assert validated is not None
    assert validated.user_id == user.user_id

    # Invalid password fails
    with pytest.raises(ValueError):
        auth.authenticate("trader1", "WrongPassword!")

    # Logout invalidates session
    auth.logout(session.token)
    assert auth.validate_session(session.token) is None
