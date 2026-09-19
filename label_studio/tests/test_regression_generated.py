import pytest
from django.test import TestCase

from projects.functions.next_task import _try_breadth_first
from projects.models import Project
from tasks.models import Task
from projects.tests.factories import ProjectFactory
from tasks.tests.factories import TaskFactory, AnnotationFactory
from users.tests.factories import UserFactory


class TestBreadthFirstExcludesUserAnnotatedTasks(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.user = UserFactory()
        cls.other_user = UserFactory()

        # Project (evaluation flag irrelevant for this test)
        cls.project = ProjectFactory(maximum_annotations=3, annotator_evaluation_enabled=False)

        # Tasks
        cls.task_user_annotated = TaskFactory(project=cls.project)
        cls.task_other_annotated = TaskFactory(project=cls.project)

        # Both tasks receive the same number of annotations (2 each)
        # Annotations on task_user_annotated are all by `cls.user`
        AnnotationFactory.create_batch(
            2,
            task=cls.task_user_annotated,
            ground_truth=False,
            completed_by=cls.user,
        )
        # Annotations on task_other_annotated are by a different user
        AnnotationFactory.create_batch(
            2,
            task=cls.task_other_annotated,
            ground_truth=False,
            completed_by=cls.other_user,
        )

    def test_user_is_not_given_own_annotated_task(self):
        """
        When multiple tasks have the same maximum annotation count,
        a task that the requesting user has already annotated must be excluded.
        """
        tasks_qs = Task.objects.filter(project=self.project)
        result = _try_breadth_first(tasks_qs, self.user, self.project)
        assert result == self.task_other_annotated

    def test_returns_none_when_all_tasks_are_annotated_by_user(self):
        """
        If every candidate task has only annotations from the requesting user,
        _try_breadth_first should return None, allowing the next pipeline step to run.
        """
        # Create a fresh project where the only task is annotated solely by the user
        project = ProjectFactory(maximum_annotations=3, annotator_evaluation_enabled=False)
        task = TaskFactory(project=project)
        AnnotationFactory(task=task, ground_truth=False, completed_by=self.user)

        tasks_qs = Task.objects.filter(project=project)
        result = _try_breadth_first(tasks_qs, self.user, project)
        assert result is None
