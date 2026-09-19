import pytest
from organizations.tests.factories import OrganizationFactory
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory, AnnotationFactory
from users.tests.factories import UserFactory
from tasks.models import Task

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


@pytest.fixture
def organization():
    return OrganizationFactory()


@pytest.fixture
def creator(organization):
    return organization.created_by


@pytest.fixture
def project(organization, creator):
    # overlap of 2 (maximum_annotations=2, 100% cohort)
    return ProjectFactory(
        organization=organization,
        created_by=creator,
        label_config=LABEL_CONFIG,
        maximum_annotations=2,
        overlap_cohort_percentage=100,
    )


@pytest.fixture
def task(project):
    # TaskFactory respects project settings and sets overlap accordingly
    return TaskFactory(project=project)




def test_task_becomes_labeled_when_required_overlap_is_met(db, task, project):
    """
    After two different annotators have completed annotations,
    ``is_labeled`` must become True (the bug previously required three).
    """
    # first annotation
    annotator1 = UserFactory(active_organization=project.organization)
    AnnotationFactory(
        task=task,
        project=project,
        completed_by=annotator1,
        result=ANNOTATION_RESULT,
    )

    # second annotation by a different user
    annotator2 = UserFactory(active_organization=project.organization)
    AnnotationFactory(
        task=task,
        project=project,
        completed_by=annotator2,
        result=ANNOTATION_RESULT,
    )

    task.refresh_from_db()
    task.update_is_labeled()
    task.refresh_from_db()
    assert task.is_labeled is True
    # also verify that the overlap calculation matches the expected value
    assert task.get_current_overlap() == task.overlap == 2
