from test_scenarios.fix.src.auth.login import fix_login_session_timeout_bug


def test_login_session_timeout_handles_missing_expiry() -> None:
    assert fix_login_session_timeout_bug(now=10, expires_at=None) is False


def test_login_session_timeout_accepts_future_expiry() -> None:
    assert fix_login_session_timeout_bug(now=10, expires_at=20) is True
