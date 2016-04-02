from pytest import fixture

from functional.core import *


@fixture()
def checker_classes():
    """ Run all checkers in one test for optimization reason. """
    return [PreparedImagesOutputChecker]


@fixture()
def builder(tmpdir):
    return ProjectBuilder(tmpdir)


def put_transform_contents(builder, directory):
    builder.save_transform_ini(
        directory,
        "[transform]\n" +
        "justconvert: yes\n")


def test_checker_valid_page(builder, checker_classes):
    builder.create_unused_image("000-001", "0001.jpg")
    builder.create_used_image("001-002", "0001.jpg")
    builder.save_images()
    builder.save_raw_toc("utf8\n")
    put_transform_contents(builder, "000-001")
    put_transform_contents(builder, "001-002")
    builder.run_program()
    for class_ in checker_classes:
        assert builder.check(class_)


def test_checker_invalid_page(builder, checker_classes):
    builder.create_used_image("000-001", "0001.jpg")
    builder.create_unused_image("001-002", "0001.jpg")
    builder.save_images()
    builder.save_raw_toc("utf8\n")
    put_transform_contents(builder, "000-001")
    put_transform_contents(builder, "001-002")
    builder.run_program()
    for class_ in checker_classes:
        assert not builder.check(class_)


def test_checker_valid_order(builder, checker_classes):
    builder.create_used_image("000-001", "0000.jpg")
    builder.create_used_image("000-001", "0001.jpg")
    builder.save_images()
    builder.save_raw_toc("utf8\n")
    put_transform_contents(builder, "000-001")
    builder.run_program()
    for class_ in checker_classes:
        assert builder.check(class_)


def test_checker_invalid_order(builder, checker_classes):
    builder.create_used_image("000-001", "0001.jpg")
    builder.create_used_image("000-001", "0000.jpg")
    builder.save_images()
    builder.save_raw_toc("utf8\n")
    put_transform_contents(builder, "000-001")
    builder.run_program()
    for class_ in checker_classes:
        assert not builder.check(class_)
