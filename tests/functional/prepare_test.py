from functional.core import (
        builder,
        PreparedImagesOutputChecker)


def postprocess_builder(builder):
    builder.save_images()
    builder.save_toc([])
    builder.save_config("[global]\ntargets: prepare")


def adjust_mtime(path, delta):
    return path.setmtime(path.mtime() + delta)


def test_subdir_order(builder):
    builder.create_unused_image("000-002", "0001.jpg")
    builder.create_used_image("001-002", "0001.jpg")
    builder.create_used_image("000-002", "0002.jpg")
    postprocess_builder(builder)
    adjust_mtime(builder.path().join("input", "001-002", "0001.jpg"), -1000)
    builder.save_transform_ini("000-002", "[transform]\njustconvert: yes\n")
    builder.save_transform_ini("001-002", "[transform]\njustconvert: yes\n")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_image_depends_on_transform(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(30, 30, 30, 30, (0, 0, 0))
        .border_count_to_check(0))
    postprocess_builder(builder)

    builder.save_transform_ini("000-001", "[transform]\njustconvert: yes\n")
    adjust_mtime(builder.path().join("input", "000-001", "0000.jpg"), -1000)
    adjust_mtime(builder.path().join("input", "000-001", "transform.ini"), -1000)
    builder.run_program()
    assert not builder.valid(PreparedImagesOutputChecker)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "chop-background: black\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_justconvert_priority(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(30, 30, 30, 30, (0, 0, 0))
        .border_count_to_check(1))
    postprocess_builder(builder)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "justconvert: yes\n" +
                               "chop-background: black\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_background_color(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(30, 30, 30, 30, (0, 0, 255))
        .border_count_to_check(0))
    postprocess_builder(builder)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "chop-background: blue\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_chop_edge(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(0, 60, 60, 0, (0, 0, 255))
        .add_border(30, 0, 0, 30, (0, 255, 0)))
    (builder.override_reference_image()
        .add_border(0, 0, 60, 0, (0, 0, 255))
        .add_border(30, 0, 0, 30, (0, 255, 0)))
    postprocess_builder(builder)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "chop-background: blue\n" +
                               "chop-edge: North\n" +
                               "chop-size: 35\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_chop_size(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(0, 60, 60, 0, (0, 0, 255))
        .add_border(30, 0, 0, 30, (0, 255, 0))
        .border_count_to_check(2))
    postprocess_builder(builder)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "chop-background: blue\n" +
                               "chop-edge: North West\n" +
                               "chop-size: 20\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)
