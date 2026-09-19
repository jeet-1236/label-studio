import pytest
from organizations.tests.factories import OrganizationFactory
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import AnnotationFactory, TaskFactory
from users.tests.factories import UserFactory

LABEL_CONFIG = (
    '<View><Text name="text" value="$text"/><Choices name="label" toName="text">'
    '<Choice value="pos"/><Choice value="neg"/></Choices></View>'
)
ANNOTATION_RESULT = [
    {
        "value": {"choices": ["pos"]},
        "from_name": "label",
        "to_name": "text",
        "type": "choices",
    }
]


@pytest.mark.django_db
def test_task_is_labeled_becomes_true_when_overlap_reached():
    # Setup organization and project with overlap of 2
    org = OrganizationFactory()
    creator = org.created_by
    project = ProjectFactory(
        organization=org,
        created_by=creator,
        label_config=LABEL_CONFIG,
        maximum_annotations=2,
        overlap_cohort_percentage=100,
    )
    # Create a task; overlap is derived from project settings (should be 2)
    task = TaskFactory(project=project)

    # Initially the task should not be labeled
    assert task.is_labeled is False

    # First annotation – still not labeled
    annotator1 = UserFactory(active_organization=org)
    AnnotationFactory(
        task=task,
        project=project,
        completed_by=annotator1,
        result=ANNOTATION_RESULT,
    )
    task.refresh_from_db()
    task.update_is_labeled()
    assert task.is_labeled is False

    # Second distinct annotator – now labeled
    annotator2 = UserFactory(active_organization=org)
    AnnotationFactory(
        task=task,
        project=project,
        completed_by=annotator2,
        result=ANNOTATION_RESULT,
    )
    task.refresh_from_db()
    task.update_is_labeled()
    assert task.is_labeled is True


@pytest.mark.django_db
def test_is_labeled_stays_true_after_exceeding_overlap():
    org = OrganizationFactory()
    creator = org.created_by

    for overlap in (1, 2, 3):
        project = ProjectFactory(
            organization=org,
            created_by=creator,
            label_config=LABEL_CONFIG,
            maximum_annotations=overlap,
            overlap_cohort_percentage=100,
        )
        task = TaskFactory(project=project)

        # Add exactly `overlap` distinct annotations
        for _ in range(overlap):
            annotator = UserFactory(active_organization=org)
            AnnotationFactory(
                task=task,
                project=project,
                completed_by=annotator,
                result=ANNOTATION_RESULT,
            )
        task.refresh_from_db()
        task.update_is_labeled()
        assert task.is_labeled is True, f"Task should be labeled at overlap {overlap}"

        # Add one more annotation; task should remain labeled
        extra_annotator = UserFactory(active_organization=org)
        AnnotationFactory(
            task=task,
            project=project,
            completed_by=extra_annotator,
            result=ANNOTATION_RESULT,
        )
        task.refresh_from_db()
        task.update_is_labeled()
        assert task.is_labeled is True, f"Task should stay labeled after exceeding overlap {overlap}"
