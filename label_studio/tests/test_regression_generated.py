import pytest
from urllib.parse import urlparse, parse_qs

@pytest.mark.django_db
def test_signup_without_token_is_forbidden(client, settings):
    # When the setting disables sign‑up without an invite link, a request with no token must be rejected.
    settings.DISABLE_SIGNUP_WITHOUT_LINK = True
    response = client.post(
        "/user/signup",
        data={"email": "no_token@example.com", "password": "test_password"},
    )
    assert response.status_code == 403
