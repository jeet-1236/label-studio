import pytest
from rest_framework.test import APIClient
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organization():
    return OrganizationFactory()


@pytest.fixture
def owner(organization):
    # The creator of the organization is the owner
    return organization.created_by


@pytest.fixture
def member(organization):
    return UserFactory(active_organization=organization)


@pytest.fixture
def other_member(organization):
    return UserFactory(active_organization=organization)


@pytest.mark.django_db
def test_owner_can_delete_member(api_client, owner, member):
    api_client.force_authenticate(user=owner)

    response = api_client.delete(f"/api/users/{member.id}/")

    assert response.status_code == 204
    assert not User.objects.filter(pk=member.id).exists()
