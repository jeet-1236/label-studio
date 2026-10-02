from unittest.mock import patch
import pytest
from django.db import OperationalError

from core.utils.db import batch_update_with_retry, fast_first
from projects.tests.factories import ProjectFactory
from tasks.models import Task
from tasks.tests.factories import TaskFactory


def test_batch_update_with_retry_updates_all_tasks(db):
    """
    Regression test for the overlap‑update bug:
    after calling ``batch_update_with_retry`` all selected tasks must have the new overlap value.
    """
    project = ProjectFactory(overlap_cohort_percentage=50, maximum_annotations=3)

    # create a handful of tasks belonging to the project
    tasks = TaskFactory.create_batch(12, project=project, overlap=1)
    task_ids = [t.id for t in tasks]

    qs = Task.objects.filter(id__in=task_ids)

    # apply the update in batches of 5
    batch_update_with_retry(qs, batch_size=5, overlap=2)

    # every task should now have overlap == 2
    assert Task.objects.filter(id__in=task_ids, overlap=2).count() == len(task_ids)


def test_batch_update_with_retry_retries_on_deadlock(db):
    """
    Ensure the retry logic is exercised when a deadlock is reported.
    The first call to ``update`` raises an OperationalError containing
    ``'deadlock detected'``; the second call succeeds.
    """
    project = ProjectFactory(overlap_cohort_percentage=30, maximum_annotations=3)
    tasks = TaskFactory.create_batch(4, project=project, overlap=1)
    task_ids = [t.id for t in tasks]
    qs = Task.objects.filter(id__in=task_ids)

    call_counter = {"updates": 0}

    original_filter = Task.objects.filter

    def flaky_filter(*args, **kwargs):
        """First update raises a deadlock, subsequent updates succeed."""
        mock_qs = original_filter(*args, **kwargs)

        original_update = mock_qs.update

        def wrapped_update(**fields):
            call_counter["updates"] += 1
            if call_counter["updates"] == 1:
                raise OperationalError("deadlock detected")
            return original_update(**fields)

        mock_qs.update = wrapped_update
        return mock_qs

    with patch.object(Task.objects, "filter", side_effect=flaky_filter):
        batch_update_with_retry(qs, batch_size=2, overlap=3)

    # after the retry the overlap must be updated for all tasks
    assert Task.objects.filter(id__in=task_ids, overlap=3).count() == len(task_ids)
    # ensure that the update was attempted at least twice (deadlock + retry)
    assert call_counter["updates"] >= 2
