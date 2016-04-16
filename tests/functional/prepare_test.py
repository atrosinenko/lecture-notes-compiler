from functional.core import (
        builder,
        PreparedImagesOutputChecker)


def _postprocess_builder(builder):
    builder.save_images()
    builder.save_toc([])
    builder.save_config("[global]\ntargets: prepare")


def _adjust_mtime(path, delta):
    return path.setmtime(path.mtime() + delta)


def test_subdir_order(builder):
    builder.create_unused_image("000-002", "0001.jpg")
    builder.create_used_image("001-002", "0001.jpg")
    builder.create_used_image("000-002", "0002.jpg")
    _postprocess_builder(builder)
    _adjust_mtime(builder.path().join("input", "001-002", "0001.jpg"), -1000)
    builder.save_transform_ini("000-002", "[transform]\njustconvert: yes\n")
    builder.save_transform_ini("001-002", "[transform]\njustconvert: yes\n")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)


def test_image_depends_on_transform(builder):
    (builder.create_used_image("000-001", "0000.jpg")
        .add_border(30, 30, 30, 30, (0, 0, 0))
        .border_count_to_check(0))
    _postprocess_builder(builder)

    builder.save_transform_ini("000-001", "[transform]\njustconvert: yes\n")
    transform_file = builder.path().join("input", "000-001", "transform.ini")
    _adjust_mtime(transform_file, -1000)
    builder.run_program()
    assert not builder.valid(PreparedImagesOutputChecker)

    builder.save_transform_ini("000-001",
                               "[transform]\n" +
                               "chop-background: black\n" +
                               "blur: 0")
    builder.run_program()
    assert builder.valid(PreparedImagesOutputChecker)
