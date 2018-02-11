from functional.core import ExampleImage


def check_valid(source_image, reference_image):
    data = source_image.create_image()
    assert reference_image.valid_image(data)


def check_invalid(source_image, reference_image):
    data = source_image.create_image()
    assert not reference_image.valid_image(data)


def test_image_check_valid_color():
    check_valid(
        ExampleImage(123, True),
        ExampleImage(123, True))


def test_image_check_valid_color_borders():
    check_valid(
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100)),
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100)))


def test_image_check_valid_color_borders_crop():
    check_valid(
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0)),
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .add_border(20, 10, 0, 30, (0, 200, 100))
            .border_count_to_check(1))


def test_image_check_valid_bw():
    check_valid(
        ExampleImage(123, False),
        ExampleImage(123, False))


def test_image_check_valid_bw_borders():
    check_valid(
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50),
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50))


def test_image_check_valid_bw_borders_crop():
    check_valid(
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100),
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .add_border(20, 10, 0, 30, 50)
            .border_count_to_check(1))


def test_image_check_invalid_color():
    check_invalid(
        ExampleImage(1023, True),
        ExampleImage(1022, True))
    check_invalid(
        ExampleImage(1023, True),
        ExampleImage(511, True))


def test_image_check_invalid_color_borders():
    check_invalid(
        ExampleImage(123, True)
            .add_border(10, 20, 30, 40, (100, 200, 100)),
        ExampleImage(123, True)
            .add_border(10, 0, 0, 40, (100, 200, 100)))


def test_image_check_invalid_color_borders_crop():
    check_invalid(
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0)),
        ExampleImage(123, True)
            .add_border(10, 0, 20, 30, (100, 100, 0))
            .border_count_to_check(0))


def test_image_check_invalid_bw():
    check_invalid(
        ExampleImage(1023, False),
        ExampleImage(1022, False))
    check_invalid(
        ExampleImage(1023, False),
        ExampleImage(511, False))


def test_image_check_invalid_bw_borders():
    check_invalid(
        ExampleImage(123, False)
            .add_border(10, 20, 30, 40, 100),
        ExampleImage(123, False)
            .add_border(10, 0, 0, 40, 100))


def test_image_check_invalid_bw_borders_crop():
    check_invalid(
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100),
        ExampleImage(123, False)
            .add_border(10, 0, 20, 30, 100)
            .border_count_to_check(0))


def test_image_check_invalid_mixed():
    check_invalid(
        ExampleImage(123, True),
        ExampleImage(123, False))
    check_invalid(
        ExampleImage(123, False),
        ExampleImage(123, True))


def test_image_check_valid_rotation():
    check_valid(
        ExampleImage(1, True),
        ExampleImage(512, True)
            .set_validation_rotation(180))


def test_image_check_invalid_rotation():
    check_invalid(
        ExampleImage(1, True),
        ExampleImage(1, True)
            .set_validation_rotation(180))


def test_image_check_valid_file(tmpdir):
    image1 = ExampleImage(123, True)
    image2 = ExampleImage(123, True)
    filename = str(tmpdir.join("image.jpg"))
    image1.save(filename)
    assert image2.valid(filename)


def test_image_check_invalid_file(tmpdir):
    image1 = ExampleImage(123, True)
    image2 = ExampleImage(321, True)
    filename = str(tmpdir.join("image.jpg"))
    image1.save(filename)
    assert not image2.valid(filename)
