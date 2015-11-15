# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function


class MockUi:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        self.progress = -1

    def error(self, *args, **kwargs):
        self.errors += 1

    def warning(self, *args, **kwargs):
        self.warnings += 1

    def progress_before(self, *args, **kwargs):
        pass

    def progress_current(self, amount):
        self.progress = amount

    def progress_after(self, *args, **kwargs):
        pass

    def progress_finalize(self, *args, **kwargs):
        pass
