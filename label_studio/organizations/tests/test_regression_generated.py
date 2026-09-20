import pytest
from unittest import mock

from organizations.models import OrganizationMember
from organizations.tests.factories import OrganizationFactory
from projects.tests.factories import ProjectFactory
from tasks.models import TaskLock
from tasks.tests.factories import TaskFactory, TaskLockFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_soft_delete_clears_avatar_and_task_locks_for_last_membership():
    # Setup: single organization, user with avatar and a task lock
    organization = OrganizationFactory()
    user = UserFactory(active_organization=organization)
    user.avatar.name = "avatars/test.png"
    user.save(update_fields=["avatar"])

    project = ProjectFactory(organization=organization)
    task = TaskFactory(project=project)
    task_lock = TaskLockFactory(user=user, task=task)

    membership = OrganizationMember.objects.get(user=user, organization=organization)

    with mock.patch.object(user.avatar.storage, "delete") as storage_delete:
        membership.soft_delete()

    user.refresh_from_db()
    membership.refresh_from_db()

    assert membership.deleted_at is not None
    assert user.active_organization is None
    assert not user.avatar
    storage_delete.assert_called_once_with("avatars/test.png")
    assert not TaskLock.objects.filter(pk=task_lock.pk).exists()


@pytest.mark.django_db
def test_soft_delete_switches_active_organization_when_multiple_memberships():
    # Setup: user belongs to two organizations
    org_primary = OrganizationFactory()
    org_secondary = OrganizationFactory()
    user = UserFactory(active_organization=org_primary)

    # Add user to secondary organization (membership not deleted)
    secondary_membership = OrganizationMember.objects.create(user=user, organization=org_secondary)

    # Create a project and task lock in the primary organization
    primary_project = ProjectFactory(organization=org_primary)
    primary_task = TaskFactory(project=primary_project)
    primary_lock = TaskLockFactory(user=user, task=primary_task)

    # Create a project and task lock in the secondary organization (should remain after soft delete)
    secondary_project = ProjectFactory(organization=org_secondary)
    secondary_task = TaskFactory(project=secondary_project)
    secondary_lock = TaskLockFactory(user=user, task=secondary_task)

    primary_membership = OrganizationMember.objects.get(user=user, organization=org_primary)

    # Perform soft delete on the primary membership
    primary_membership.soft_delete()

    user.refresh_from_db()
    primary_membership.refresh_from_db()
    secondary_membership.refresh_from_db()

    # The primary membership should be marked deleted
    assert primary_membership.deleted_at is not None
    # User's active organization should now point to the secondary organization
    assert user.active_organization_id == org_secondary.id
    # Task lock belonging to the primary organization should be removed
    assert not TaskLock.objects.filter(pk=primary_lock.pk).exists()
    # Task lock belonging to the secondary organization should still exist
    assert TaskLock.objects.filter(pk=secondary_lock.pk).exists()
    # The secondary membership should remain active
    assert secondary_membership.deleted_at is None
