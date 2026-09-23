import pytest
from tasks.models import Task, Annotation
from projects.models import Project




@pytest.mark.django_db
def test_ground_truth_switches_within_same_task():
    # Setup a project with a single task that has two annotations
    project = Project.objects.create(title="Switch Test Project")
    task = Task.objects.create(project=project, data={})

    ann1 = Annotation.objects.create(task=task, result={}, ground_truth=False)
    ann2 = Annotation.objects.create(task=task, result={}, ground_truth=False)

    # First annotation becomes ground truth
    ann1.ground_truth = True
    ann1.save()
    task.ensure_unique_groundtruth(ann1.id)

    # Second annotation becomes ground truth, first should be cleared
    ann2.ground_truth = True
    ann2.save()
    task.ensure_unique_groundtruth(ann2.id)

    ann1.refresh_from_db()
    ann2.refresh_from_db()
    assert ann1.ground_truth is False
    assert ann2.ground_truth is True
