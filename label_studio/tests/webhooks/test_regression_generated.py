import pytest
from django.urls import reverse

from webhooks.models import Webhook
from webhooks.serializers import WebhookSerializer


@pytest.fixture
def webhook_instance(configured_project):
    """Create a generic webhook attached to the organization (no project)."""
    organization = configured_project.organization
    return Webhook.objects.create(
        organization=organization,
        project=None,
        url="http://example.com/initial",
        is_active=False,
        consecutive_failures=42,
    )


@pytest.mark.django_db
def test_reactivate_resets_failure_counter(webhook_instance):
    """
    When a webhook is re‑activated (is_active changes from False to True),
    the serializer should reset ``consecutive_failures`` to 0.
    """
    serializer = WebhookSerializer(
        instance=webhook_instance,
        data={"is_active": True},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()
    assert updated.is_active is True
    assert updated.consecutive_failures == 0
