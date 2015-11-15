# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function

from time import sleep, time

from tests.mock.ui import MockUi
import lnc.main


def create_variables(func, task_count):
    """Use task list returned by this function because run_tasks_in_parallel()
    modifies task list that was passed to it."""
    tasks = []
    for i in range(task_count):
        tasks.append({"__handler__": func, "count": 0, "index": i})
    variables = lnc.main.Variables(MockUi(), "target", tasks)

    return variables, [task for task in tasks]


def run_tasks(task_count, jobs):
    def func(x):
        x["count"] += 1

    variables, tasks = create_variables(func, task_count)
    lnc.main.run_tasks_in_parallel(variables, jobs)

    assert(len(variables.errors) == 0)
    assert(len(tasks) == task_count)
    for task in tasks:
        assert(task["count"] == 1)


def test_run_tasks_single_threaded():
    run_tasks(1000, 1)


def test_run_tasks_multi_threaded():
    run_tasks(1000, 10)


def test_run_tasks_many_threads():
    run_tasks(10, 100)


def run_failing_tasks(task_count, jobs):
    def func(x):
        x["count"] += 1
        raise Exception()

    variables, tasks = create_variables(func, task_count)
    lnc.main.run_tasks_in_parallel(variables, jobs)

    total = 0
    assert(len(tasks) == task_count)
    for task in tasks:
        total += task["count"]

    assert(len(variables.errors) > 0)
    assert(total >= 1)
    assert(total <= jobs)


def test_run_failing_tasks_single_threaded():
    run_failing_tasks(1000, 1)


def test_run_failing_tasks_multi_threaded():
    run_failing_tasks(1000, 10)


def test_run_failing_tasks_many_threads():
    run_failing_tasks(10, 100)


def run_tasks_one_fail(task_count, jobs):
    def func(x):
        x["count"] += 1
        if x["index"] == task_count / 2:
            raise Exception()

    variables, _ = create_variables(func, task_count)
    lnc.main.run_tasks_in_parallel(variables, jobs)

    assert(len(variables.errors) > 0)


def test_run_tasks_one_fail_single_threaded():
    run_tasks_one_fail(1000, 1)


def test_run_tasks_one_fail_multi_threaded():
    run_tasks_one_fail(1000, 10)


def test_run_tasks_one_fail_many_threads():
    run_tasks_one_fail(10, 100)


def test_execution_time():
    def func(x):
        x["count"] += 1
        sleep(0.1)

    variables, _ = create_variables(func, 300)
    start_time = time()
    lnc.main.run_tasks_in_parallel(variables, 10)
    total_time = time() - start_time

    assert(total_time > 2.99)
    assert(total_time < 3.1)
