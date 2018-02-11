from pytest import fixture

from functional.core import (
        builder,
        PreparedImagesOutputChecker,
        PDFDocumentChecker,
        DjVuDocumentChecker)


@fixture()
def checker_classes():
    """ Run all checkers in one test for optimization reason. """
    return [
        PreparedImagesOutputChecker,
        PDFDocumentChecker,
        DjVuDocumentChecker]


@fixture()
def toc_checker_classes():
    return [PDFDocumentChecker, DjVuDocumentChecker]


def put_transform_contents(builder, directory):
    builder.save_transform_ini(
        directory,
        "[transform]\n" +
        "justconvert: yes\n")


def check_all_valid(builder, checkers):
    for class_ in checkers:
        assert builder.valid(class_)


def check_all_invalid(builder, checkers):
    for class_ in checkers:
        assert not builder.valid(class_)


def test_checker_valid_page(builder, checker_classes):
    builder.create_unused_image("000-001", "0001.jpg")
    builder.create_used_image("001-002", "0001.jpg")
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    put_transform_contents(builder, "001-002")
    builder.run_program()
    check_all_valid(builder, checker_classes)


def test_checker_invalid_page(builder, checker_classes):
    builder.create_used_image("000-001", "0001.jpg")
    builder.create_unused_image("001-002", "0001.jpg")
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    put_transform_contents(builder, "001-002")
    builder.run_program()
    check_all_invalid(builder, checker_classes)


def test_checker_valid_order(builder, checker_classes):
    builder.create_used_image("000-001", "0000.jpg")
    builder.create_used_image("000-001", "0001.jpg")
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    builder.run_program()
    check_all_valid(builder, checker_classes)


def test_checker_valid_reference_override(builder, checker_classes):
    builder.create_used_image("000-001", "0000.jpg")
    builder.override_reference_image()
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    builder.run_program()
    check_all_valid(builder, checker_classes)


def test_checker_invalid_reference_override(builder, checker_classes):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(20, 20, 20, 20, (0, 0, 0)))
    (builder.override_reference_image()
        .add_border(50, 50, 50, 50, (0, 0, 0)))
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    builder.run_program()
    check_all_invalid(builder, checker_classes)


def test_checker_invalid_order(builder, checker_classes):
    builder.create_used_image("000-001", "0001.jpg")
    builder.create_used_image("000-001", "0000.jpg")
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-001")
    builder.run_program()
    check_all_invalid(builder, checker_classes)


def test_checker_invalid_count(builder, checker_classes):
    builder.create_used_image("000-002", "0000.jpg")
    builder.create_used_image("000-002", "0001.jpg")
    builder.create_unused_image("000-002", "0002.jpg")
    builder.save_images()
    builder.save_toc([])
    put_transform_contents(builder, "000-002")
    builder.run_program()
    check_all_invalid(builder, checker_classes)


def prepare_three_images(builder):
    for i in range(1, 4):
        builder.create_used_image("001-003", "%04d.jpg" % i)
    builder.save_images()
    put_transform_contents(builder, "001-003")


def test_checker_valid_toc(builder, toc_checker_classes):
    prepare_three_images(builder)
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"],
        [0, 3, "Page 3"]
    ])
    builder.run_program()
    check_all_valid(builder, toc_checker_classes)


def test_checker_invalid_level_toc(builder, toc_checker_classes):
    prepare_three_images(builder)
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"]
    ])
    builder.run_program()
    builder.save_toc([
        [0, 1, "Page 1"],
        [0, 2, "Page 2"]
    ])
    check_all_invalid(builder, toc_checker_classes)


def test_checker_invalid_pagenum_toc(builder, toc_checker_classes):
    prepare_three_images(builder)
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"]
    ])
    builder.run_program()
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 3, "Page 2"]
    ])
    check_all_invalid(builder, toc_checker_classes)


def test_checker_invalid_description_toc(builder, toc_checker_classes):
    prepare_three_images(builder)
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"]
    ])
    builder.run_program()
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2 2 2"]
    ])
    check_all_invalid(builder, toc_checker_classes)


def test_checker_invalid_toc_extra_line(builder, toc_checker_classes):
    prepare_three_images(builder)
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"]
    ])
    builder.run_program()
    builder.save_toc([
        [0, 1, "Page 1"],
        [1, 2, "Page 2"],
        [2, 3, "Page 3"]
    ])
    check_all_invalid(builder, toc_checker_classes)
