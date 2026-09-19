import pytest
from unittest.mock import MagicMock

from data_manager.api import TaskPagination
from tasks.models import Task
from tasks.tests.factories import TaskFactory, AnnotationFactory, PredictionFactory
from projects.tests.factories import ProjectFactory
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_task_pagination_aggregates_correct_counts():
    # Set up organization, user and project
    org = OrganizationFactory()
    user = UserFactory()
    user.active_organization = org
    user.save()
    project = ProjectFactory(organization=org)

    # Task 1: 3 annotations, 0 predictions
    task1 = TaskFactory(project=project)
    for _ in range(3):
        AnnotationFactory(task=task1)

    # Task 2: 0 annotations, 2 predictions
    task2 = TaskFactory(project=project)
    for _ in range(2):
        PredictionFactory(task=task2)

    # Refresh denormalized counters
    task1.refresh_from_db()
    task2.refresh_from_db()

    # Mock request with pagination params and authenticated user
    request = MagicMock()
    request.query_params = {"page": "1", "page_size": "10"}
    request.user = user

    pagination = TaskPagination()
    queryset = Task.objects.filter(project=project)

    # Perform pagination (the method returns the page slice, which we ignore)
    pagination.paginate_queryset(queryset, request)

    # Verify that totals reflect the actual annotation/prediction counts
    assert pagination.total_annotations == 3
    assert pagination.total_predictions == 2
