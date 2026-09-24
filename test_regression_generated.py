import pytest
from data_export.mixins import ExportMixin
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory, AnnotationFactory


class DummyExport(ExportMixin):
    """Simple concrete class to expose the mixin methods."""
    pass


@pytest.fixture
def dummy_export():
    return DummyExport()


@pytest.fixture
def project():
    return ProjectFactory()


@pytest.fixture
def task(project):
    return TaskFactory(project=project)


@pytest.fixture
def user(project):
    return project.created_by


@pytest.fixture
def annotations(task, user):
    """
    Create three annotations on the same task:
    - regular: not cancelled, not ground truth
    - ground_truth: not cancelled, ground truth flag set
    - skipped: cancelled, not ground truth
    """
    regular = AnnotationFactory(
        task=task,
        completed_by=user,
        was_cancelled=False,
        ground_truth=False,
    )
    ground_truth = AnnotationFactory(
        task=task,
        completed_by=user,
        was_cancelled=False,
        ground_truth=True,
    )
    skipped = AnnotationFactory(
        task=task,
        completed_by=user,
        was_cancelled=True,
        ground_truth=False,
    )
    return {"regular": regular, "ground_truth": ground_truth, "skipped": skipped}


@pytest.mark.django_db
def test_filtered_annotations_multiple_kinds(dummy_export, annotations):
    """
    When both regular (usual) and ground‑truth annotations are requested,
    the queryset should contain exactly those two annotations.
    """
    qs = dummy_export._get_filtered_annotations_queryset(
        {"usual": True, "ground_truth": True}
    )
    ids = {a.id for a in qs}
    expected = {annotations["regular"].id, annotations["ground_truth"].id}
    assert ids == expected


@pytest.mark.django_db
def test_filtered_annotations_all_kinds(dummy_export, annotations):
    """
    When regular, ground‑truth and skipped annotations are all requested,
    the queryset should contain every annotation on the task.
    """
    qs = dummy_export._get_filtered_annotations_queryset(
        {"usual": True, "ground_truth": True, "skipped": True}
    )
    ids = {a.id for a in qs}
    expected = {
        annotations["regular"].id,
        annotations["ground_truth"].id,
        annotations["skipped"].id,
    }
    assert ids == expected
