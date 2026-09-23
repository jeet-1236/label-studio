import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from jwt_auth.views import LSAPITokenView


@pytest.mark.django_db
def test_lsa_token_queryset_is_scoped_to_current_user():
    """
    The Personal Access Token list must be scoped to the requesting user.
    A token created by one user should NOT appear in the queryset returned
    for a different user.

    Current buggy implementation returns all non‑expired tokens regardless
    of owner, causing other users to see and be blocked by someone else's
    token. After the fix, the queryset should contain only tokens belonging
    to ``request.user`` (i.e. be empty for a user with no tokens).
    """
    User = get_user_model()

    # Create two distinct users
    user1 = User.objects.create_user(
        username="user1", email="user1@example.com", password="pwd"
    )
    user2 = User.objects.create_user(
        username="user2", email="user2@example.com", password="pwd"
    )

    # Create a token for user1 that is still valid
    OutstandingToken.objects.create(
        user=user1,
        jti=str(uuid.uuid4()),
        token="dummy-token-1",
        created_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=1),
    )

    # Simulate a request made by user2
    factory = RequestFactory()
    request = factory.get("/fake-path/")
    request.user = user2

    # Instantiate the view and attach the request
    view = LSAPITokenView()
    view.request = request

    # The queryset should be empty for user2 (no tokens belong to them)
    qs = view.get_queryset()
    assert qs.count() == 0, "Token queryset is not scoped to the current user"
    # Additionally, ensure that no token belonging to another user leaks into the queryset
    assert not qs.filter(user=user1).exists(), "Token from another user is visible in the queryset"
