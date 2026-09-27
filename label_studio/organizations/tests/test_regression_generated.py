from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from organizations.serializers import OrganizationSerializer
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory


class TestOrganizationSerializerReadOnlyOwner(TestCase):
    def setUp(self):
        self.organization = OrganizationFactory()
        self.owner = self.organization.created_by
        self.member = UserFactory(active_organization=self.organization)

    def test_serializer_ignores_created_by_on_update(self):
        # Attempt to change ownership via serializer data
        data = {
            "title": "Updated Title",
            "created_by": self.member.id,  # should be ignored because read_only
        }
        serializer = OrganizationSerializer(
            instance=self.organization, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        # Reload from DB and ensure owner unchanged
        self.organization.refresh_from_db()
        assert self.organization.created_by_id == self.owner.id
        # Ensure other fields were updated
        assert self.organization.title == "Updated Title"


class TestOrganizationUpdateAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.owner = self.organization.created_by
        self.member = UserFactory(active_organization=self.organization)

    def test_member_cannot_take_ownership_via_patch(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(
            f"/api/organizations/{self.organization.id}",
            {"created_by": self.member.id},
            format="json",
        )
        assert response.status_code == 200

        self.organization.refresh_from_db()
        assert self.organization.created_by_id == self.owner.id

    def test_member_cannot_take_ownership_via_put(self):
        self.client.force_authenticate(user=self.member)

        # Include required fields for a full update; assume 'title' is required
        response = self.client.put(
            f"/api/organizations/{self.organization.id}",
            {
                "title": self.organization.title,
                "created_by": self.member.id,
            },
            format="json",
        )
        assert response.status_code == 200

        self.organization.refresh_from_db()
        assert self.organization.created_by_id == self.owner.id
