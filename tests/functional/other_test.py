# -*- coding: utf8 -*-
from __future__ import print_function, unicode_literals

from functional.core import (
        builder,
        PDFDocumentChecker,
        DjVuDocumentChecker)


def check_all_valid(builder):
    for class_ in [PDFDocumentChecker, DjVuDocumentChecker]:
        assert builder.valid(class_)


def test_toc(builder):
    builder.create_used_image("000-010", "0000.jpg")
    builder.create_used_image("000-010", "0001.jpg")
    builder.create_used_image("000-010", "0002.jpg")
    builder.create_used_image("000-010", "0003.jpg")
    builder.create_used_image("000-010", "0004.jpg")
    builder.save_images()
    builder.save_transform_ini("000-010", "[transform]\njustconvert: yes")
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Страница 2"],
        [2, 3, "'Quotes\""],
        [0, 5, "Page 5"]])
    builder.run_program()
    check_all_valid(builder)
