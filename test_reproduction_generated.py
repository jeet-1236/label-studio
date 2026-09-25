import pytest
from unittest import mock

from django.contrib.auth import get_user_model

from tasks.functions import bulk_create_annotations_with_side_effects
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory
from tasks.models import Annotation


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="tester", email="tester@example.com", password="test"
    )


@pytest.fixture
def project(db):
    return ProjectFactory()


@pytest.fixture
def task(db, project):
    return TaskFactory(project=project)


def make_annotation(task, user):
    """
    Create a minimal unsaved Annotation instance suitable for bulk_create.
    The fields required by the model are task, result and completed_by.
    """
    return Annotation(task=task, result={}, completed_by=user)


def test_bulk_create_annotations_respects_update_project_summary_flag(monkeypatch, project, task, user):
    """
    The ``update_project_summary`` flag should control whether the project's
    summary is updated. The current implementation incorrectly updates the
    summary unconditionally because of the ``or hasattr(project, 'summary')``
    guard. This test verifies that the guard respects the flag.
    """
    # Replace the summary method with a mock that records calls
    mock_update = mock.Mock()
    monkeypatch.setattr(project.summary, "update_created_annotations_and_labels", mock_update)

    # First call with the flag disabled – the summary must NOT be updated
    ann1 = make_annotation(task, user)
    bulk_create_annotations_with_side_effects(
        [ann1],
        project=project,
        user=user,
        action="create",
        update_project_summary=False,
        tasks_queryset=[task.id],
    )
    assert mock_update.call_count == 0, "Summary was updated despite update_project_summary=False"

    # Second call with the flag enabled – the summary MUST be updated exactly once
    ann2 = make_annotation(task, user)
    bulk_create_annotations_with_side_effects(
        [ann2],
        project=project,
        user=user,
        action="create",
        update_project_summary=True,
        tasks_queryset=[task.id],
    )
    assert mock_update.call_count == 1, "Summary was not updated when update_project_summary=True"


def test_bulk_create_annotations_updates_summary_when_flag_true(monkeypatch, project, task, user):
    """
    When ``update_project_summary`` is True (the default), the project's summary
    must be updated. This test ensures the positive path works.
    """
    mock_update = mock.Mock()
    monkeypatch.setattr(project.summary, "update_created_annotations_and_labels", mock_update)

    ann = make_annotation(task, user)
    bulk_create_annotations_with_side_effects(
        [ann],
        project=project,
        user=user,
        action="create",
        # leave flag at default (True)
        tasks_queryset=[task.id],
    )
    assert mock_update.called, "Summary was not updated when update_project_summary is True"
