import pytest
from django.db.models import QuerySet

from projects.functions import annotate_total_annotations_number
from projects.models import Project
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory, AnnotationFactory


@pytest.mark.django_db
def test_total_annotations_excludes_cancelled():
    # Create a project with three tasks
    project = ProjectFactory()
    tasks = [TaskFactory(project=project) for _ in range(3)]

    # Two real annotations (was_cancelled=False), one skipped (was_cancelled=True)
    AnnotationFactory(task=tasks[0], project=project, was_cancelled=False)
    AnnotationFactory(task=tasks[1], project=project, was_cancelled=False)
    AnnotationFactory(task=tasks[2], project=project, was_cancelled=True)

    qs: QuerySet = Project.objects.filter(id=project.id)
    annotated_qs = annotate_total_annotations_number(qs)
    annotated = annotated_qs.first()

    # Only the two non‑cancelled annotations should be counted
    assert annotated.total_annotations_number == 2


@pytest.mark.django_db
def test_total_annotations_zero_when_all_skipped():
    # Create a project with two tasks, both skipped
    project = ProjectFactory()
    tasks = [TaskFactory(project=project) for _ in range(2)]

    AnnotationFactory(task=tasks[0], project=project, was_cancelled=True)
    AnnotationFactory(task=tasks[1], project=project, was_cancelled=True)

    qs: QuerySet = Project.objects.filter(id=project.id)
    annotated = annotate_total_annotations_number(qs).first()

    # No non‑cancelled annotations exist, count should be zero
    assert annotated.total_annotations_number == 0


@pytest.mark.django_db
def test_annotation_counts_are_correct_across_multiple_projects():
    # Project A: 1 real annotation, 1 skipped
    proj_a = ProjectFactory()
    task_a1 = TaskFactory(project=proj_a)
    task_a2 = TaskFactory(project=proj_a)
    AnnotationFactory(task=task_a1, project=proj_a, was_cancelled=False)
    AnnotationFactory(task=task_a2, project=proj_a, was_cancelled=True)

    # Project B: 2 real annotations, no skips
    proj_b = ProjectFactory()
    task_b1 = TaskFactory(project=proj_b)
    task_b2 = TaskFactory(project=proj_b)
    AnnotationFactory(task=task_b1, project=proj_b, was_cancelled=False)
    AnnotationFactory(task=task_b2, project=proj_b, was_cancelled=False)

    qs = Project.objects.filter(id__in=[proj_a.id, proj_b.id])
    annotated_qs = annotate_total_annotations_number(qs)

    results = {p.id: p.total_annotations_number for p in annotated_qs}
    assert results[proj_a.id] == 1  # only the non‑cancelled annotation
    assert results[proj_b.id] == 2  # both annotations count
