import math

import pytest
from django.conf import settings

from core.utils.common import paginator, safe_float


class DummyRequest:
    def __init__(self, get_dict):
        self.GET = get_dict


def test_paginator_returns_all_objects_when_page_size_minus_one():
    objects = list(range(10))
    request = DummyRequest({"page_size": "-1"})
    result = paginator(objects, request)
    assert result == objects, "Paginator should return the original iterable when page_size is '-1'"
