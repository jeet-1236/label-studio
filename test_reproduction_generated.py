import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from label_studio.jwt_auth.views import LSAPITokenView


@pytest.mark.django_db
def test_token_queryset_is_scoped_to_current_user():
    """
    The Personal Access Token list endpoint must return only the tokens that belong to
    the requesting user. The current implementation returns all non‑expired tokens,
    ignoring the user, which causes other users' tokens to appear and blocks token
    creation for new users.
    """
    User = get_user_model()
    # Create two distinct users
    user_a = User.objects.create_user(username="user_a", email="a@example.com", password="pwd")
    user_b = User.objects.create_user(username="user_b", email="b@example.com", password="pwd")

    # Create a valid token for each user
    now = timezone.now()
    expires = now + timedelta(days=1)

    token_a = OutstandingToken.objects.create(
        user=user_a,
        jti="jti-a",
        token="token-a",
        created_at=now,
        expires_at=expires,
    )
    token_b = OutstandingToken.objects.create(
        user=user_b,
        jti="jti-b",
        token="token-b",
        created_at=now,
        expires_at=expires,
    )

    # Simulate a request made by user_a
    factory = RequestFactory()
    request = factory.get("/api/personal-access-token/")
    request.user = user_a

    view = LSAPITokenView()
    view.request = request

    # The queryset should contain only user_a's token
    qs = view.get_queryset()
    qs_list = list(qs)

    assert len(qs_list) == 1, "Queryset should contain exactly one token for the current user"
    assert qs_list[0].user_id == user_a.id, "Returned token does not belong to the requesting user"
    assert qs_list[0].id == token_a.id, "Returned token is not the one created for the requesting user"
    # Ensure token belonging to another user is not present
    assert token_b not in qs_list, "Token belonging to another user is incorrectly included in the queryset"
