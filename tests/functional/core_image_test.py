from functional.core import TestImage


def check_valid(source_image, reference_image):
    data = source_image.create_image()
    assert reference_image.valid_image(data)


def check_invalid(source_image, reference_image):
    data = source_image.create_image()
    assert not reference_image.valid_image(data)


def test_image_check_valid_color():
    check_valid(
        TestImage(123, True),
        TestImage(123, True))


def test_image_check_valid_color_borders():
    check_valid(
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100)),
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100)))


def test_image_check_valid_color_borders_crop():
    check_valid(
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0)),
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100))
            .border_count_to_check(1))


def test_image_check_valid_bw():
    check_valid(
        TestImage(123, False),
        TestImage(123, False))


def test_image_check_valid_bw_borders():
    check_valid(
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50),
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50))


def test_image_check_valid_bw_borders_crop():
    check_valid(
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100),
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50)
            .border_count_to_check(1))


def test_image_check_invalid_color():
    check_invalid(
        TestImage(1023, True),
        TestImage(1022, True))
    check_invalid(
        TestImage(1023, True),
        TestImage(511, True))


def test_image_check_invalid_color_borders():
    check_invalid(
        TestImage(123, True)
            .add_border(10, 20, 30, 40, (100, 200, 100)),
        TestImage(123, True)
            .add_border(10, 0, 0, 40, (100, 200, 100)))


def test_image_check_invalid_color_borders_crop():
    check_invalid(
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0)),
        TestImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .border_count_to_check(0))


def test_image_check_invalid_bw():
    check_invalid(
        TestImage(1023, False),
        TestImage(1022, False))
    check_invalid(
        TestImage(1023, False),
        TestImage(511, False))


def test_image_check_invalid_bw_borders():
    check_invalid(
        TestImage(123, False)
            .add_border(10, 20, 30, 40, 100),
        TestImage(123, False)
            .add_border(10, 0, 0, 40, 100))


def test_image_check_invalid_bw_borders_crop():
    check_invalid(
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100),
        TestImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .border_count_to_check(0))


def test_image_check_invalid_mixed():
    check_invalid(
        TestImage(123, True),
        TestImage(123, False))
    check_invalid(
        TestImage(123, False),
        TestImage(123, True))


def test_image_check_valid_rotation():
    check_valid(
        TestImage(1, True),
        TestImage(512, True)
            .set_validation_rotation(180))


def test_image_check_invalid_rotation():
    check_invalid(
        TestImage(1, True),
        TestImage(1, True)
            .set_validation_rotation(180))


def test_image_check_valid_file(tmpdir):
    image1 = TestImage(123, True)
    image2 = TestImage(123, True)
    filename = str(tmpdir.join("image.jpg"))
    image1.save(filename)
    assert image2.valid(filename)


def test_image_check_invalid_file(tmpdir):
    image1 = TestImage(123, True)
    image2 = TestImage(321, True)
    filename = str(tmpdir.join("image.jpg"))
    image1.save(filename)
    assert not image2.valid(filename)
