import pytest
from data_manager.actions.predictions_to_annotations import predictions_to_annotations
from projects.models import Project
from tasks.models import Task, Prediction, Annotation
from users.models import User


class RequestStub:
    def __init__(self, user, data=None):
        self.user = user
        self.data = data or {}


@pytest.mark.django_db
def test_predictions_to_annotations_is_idempotent():
    # Setup user and project
    user = User.objects.create(username="tester", email="tester@example.com")
    project = Project.objects.create(title="Test Project", created_by=user)

    # Create a single task and a prediction for it
    task = Task.objects.create(project=project, data={"text": "sample"})
    Prediction.objects.create(
        task=task,
        project=project,
        result=[{"from_name": "label", "to_name": "text", "type": "choices", "value": {"choices": ["pos"]}}],
        model_version="v1",
    )

    # First run – should create one annotation
    req = RequestStub(user, data={})
    resp1 = predictions_to_annotations(project, Task.objects.filter(id=task.id), request=req)
    assert resp1["response_code"] == 200
    assert Annotation.objects.filter(task=task).count() == 1

    # Second run – should not create any additional annotations
    resp2 = predictions_to_annotations(project, Task.objects.filter(id=task.id), request=req)
    assert resp2["response_code"] == 200
    assert Annotation.objects.filter(task=task).count() == 1


@pytest.mark.django_db
def test_predictions_to_annotations_respects_model_version_filter():
    # Setup user and project
    user = User.objects.create(username="filter_user", email="filter@example.com")
    project = Project.objects.create(title="Filter Project", created_by=user)

    # Create a task with two predictions of different model versions
    task = Task.objects.create(project=project, data={"text": "filter test"})
    pred_v1 = Prediction.objects.create(
        task=task,
        project=project,
        result=[{"from_name": "label", "to_name": "text", "type": "choices", "value": {"choices": ["v1"]}}],
        model_version="v1",
    )
    pred_v2 = Prediction.objects.create(
        task=task,
        project=project,
        result=[{"from_name": "label", "to_name": "text", "type": "choices", "value": {"choices": ["v2"]}}],
        model_version="v2",
    )

    # Run action filtering only for version v1
    req_v1 = RequestStub(user, data={"model_version": "v1"})
    predictions_to_annotations(project, Task.objects.filter(id=task.id), request=req_v1)

    # Only the v1 prediction should have produced an annotation
    assert Annotation.objects.filter(task=task, parent_prediction_id=pred_v1.id).count() == 1
    assert Annotation.objects.filter(task=task, parent_prediction_id=pred_v2.id).count() == 0

    # Run action again with both versions; v1 should be skipped, v2 should be added
    req_both = RequestStub(user, data={"model_version": ["v1", "v2"]})
    predictions_to_annotations(project, Task.objects.filter(id=task.id), request=req_both)

    # Now both predictions should have a single annotation each
    assert Annotation.objects.filter(task=task, parent_prediction_id=pred_v1.id).count() == 1
    assert Annotation.objects.filter(task=task, parent_prediction_id=pred_v2.id).count() == 1

    # Total annotations for the task should be exactly two
    assert Annotation.objects.filter(task=task).count() == 2
