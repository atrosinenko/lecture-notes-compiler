from __future__ import print_function, unicode_literals

from pytest import fixture
from PIL import Image, ImageDraw
import subprocess

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines


class ProjectBuilder:
    """Test project generation and result validation facility.

    ProjectBuilder writes test project to the directory specified,
    runs lnc on it and checks results. It uses the ExampleImage class to
    write test images and recognize processed output images and OutputChecker
    class to process particular output format.
    """

    def __init__(self, path):
        """Create ProjectBuilder instance that will write project to path."""

        self._used_images = []
        # A sequence of images to check generated output against

        self._image_files = []
        # An array of (file path, ExampleImage) for all registered used
        # and unused images

        self._path = path
        # Path to write project to

        self._next_id = 1
        # ID of the next created image (either used or unused)

        self._use_color = True
        # Whether to use color images or not

        self._toc = None

    def path(self):
        return self._path

    def set_color(self, use_color):
        """Toggle color image usage on/off.

        If False is passed, use black-white images for testing,
        is True is passed (the default) use color images.
        """

        self._use_color = use_color

    def create_used_image(self, directory, name):
        """Create and return a ExampleImage that should present in the output.

        Creates an image at input/directory/name that will be checked
        for presence in the output sequence in the order of calls to
        this function.
        """

        image = self._create_image(directory, name)
        self._used_images.append(image)
        return image

    def override_reference_image(self):
        """Create reference image to check previous used image against."""
        image = ExampleImage(self._next_id - 1, self._use_color)
        self._used_images[len(self._used_images) - 1] = image
        return image

    def create_unused_image(self, directory, name):
        """Create and return a ExampleImage that should not present in the output.

        Creates an image that will be placed to input/directory/name file but
        will not be checked against when checking for output correctness.
        """

        return self._create_image(directory, name)

    def save_images(self):
        """Write input image files at the places specified."""
        for path, image in self._image_files:
            path.ensure()
            image.save(str(path))

    def save_toc(self, toc):
        """Write TOC file.

        Accepts list of lists describing TOC entries:
        [
            [level, pagenum, description],
            [level, pagenum, description],
            ...
        ]
        The last saved TOC will be used for validation.
        """

        self._toc = toc
        with self._path.join("toc.txt").open(mode="w", ensure=True) as tocfile:
            print("utf8", file=tocfile)
            for entry in toc:
                line = "%s %d %s" % ("*" * entry[0], entry[1], entry[2])
                print(line.encode("utf8"), file=tocfile)

    def save_transform_ini(self, directory, contents):
        """Write contents as the transform.ini for the directory specified."""
        path = self._path.join("input", directory, "transform.ini")
        path.ensure()
        path.write(contents)

    def save_config(self, contents):
        """Write project configuration contents."""
        self._path.join("project.ini").write(contents)

    def run_program(self):
        """Run lnc on the project generated."""
        assert subprocess.call(["./lnc.py", str(self._path), "output"]) == 0

    def valid(self, checker_class):
        """Check generated output.

        Returns True if output is correct and False otherwise."""

        checker = checker_class(self._path)
        print("Checking image count...")
        if len(self._used_images) != checker.image_count():
            return False
        print("Checking TOC...")
        if not checker.valid_toc(self._toc):
            return False
        for i, image in enumerate(self._used_images):
            print("Checking image at index:", i)
            if not checker.valid_image_at_index(i, image):
                return False
        return True

    def _create_image(self, directory, name):
        image = ExampleImage(self._next_id, self._use_color)
        filepath = self._path.join("input").join(directory).join(name)
        self._next_id += 1
        self._image_files.append((filepath, image))
        return image


@fixture()
def builder(tmpdir):
    return ProjectBuilder(tmpdir)


""" Main image layout (supposed to persist lossy compression):
+------------+
|............|
|..#       #.|
|.. 01...89 .|
|..#       #.|
|............|
+------------+

#-s are black [color] / gray [BW] square markers
0-9 are squares of one of the following 2 colors:
   * green  (00FF00) [color] / white (FF) [BW]
   * blue   (0000FF) [color] / black (00) [BW]
they code a number from 0 to 1023

Each square is 64x64 pixel in size. Dots represents some areas
that may or may not be cropped by the program. Their sizes are not
necessarily multiples of 64 and colors not necessarily white.
"""


"How many bits to use to code _index"
_IMAGE_BIT_COUNT = 10

_IMAGE_SQUARE_SIDE = 64


class ExampleImage:
    def __init__(self, index, use_color):
        self._index = index
        # ID of image

        self._use_color = use_color
        # Generate and check color images

        self._borders = []
        # List of border sizes and colors (top, right, bottom, left, color)
        # from inner to outer

        self._borders_count_to_check = 0
        # Count of inner borders that should be retained

        self._validation_rotation_degrees = 0
        # Rotate before validation

    def add_border(self, up, right, down, left, color):
        self._borders.append((up, right, down, left, color))
        self._borders_count_to_check += 1
        return self

    def border_count_to_check(self, count):
        """Call after all borders are already added."""
        self._borders_count_to_check = count
        return self

    def create_image(self):
        borders = self._total_borders(is_processed=False)
        xsize, ysize = self._image_size_with_borders(borders)
        if self._use_color:
            image = Image.new("RGB", (xsize, ysize))
        else:
            image = Image.new("L", (xsize, ysize))
        draw = ImageDraw.Draw(image)

        x1, y1, x2, y2 = self._draw_borders(draw, xsize, ysize)
        self._draw_mark(draw, x1, y1, x2, y2)

        return image

    def set_validation_rotation(self, degrees):
        self._validation_rotation_degrees = degrees
        return self

    def save(self, filename):
        self.create_image().save(filename)

    def valid_image(self, image):
        if self._validation_rotation_degrees != 0:
            image = image.rotate(self._validation_rotation_degrees)
        borders = self._total_borders(is_processed=True)
        xsize, ysize = self._image_size_with_borders(borders)
        real_xsize, real_ysize = image.size
        print("Size: real =", (real_xsize, real_ysize),
              "expected =", (xsize, ysize))
        if ((self._use_color and image.mode != "RGB") or
            (not self._use_color and image.mode == "RGB")):
            print("Incorrect colorspace.")
            return False
        if not (abs(xsize - real_xsize) < 10 and
                abs(ysize - real_ysize) < 10):
            print("Incorrect size.")
            return False

        side = _IMAGE_SQUARE_SIDE
        x1 = borders[3]
        y1 = borders[0]
        x2 = x1 + (_IMAGE_BIT_COUNT + 2) * side
        y2 = y1 + 3 * side
        corner_color = (0, 0, 0) if self._use_color else 128
        if not (self._check_color(image, x1, y1, corner_color) and
                self._check_color(image, x1, y2 - side, corner_color) and
                self._check_color(image, x2 - side, y1, corner_color) and
                self._check_color(image, x2 - side, y2 - side, corner_color)):
            print("Incorrect corners")
            return False

        x = x2 - 2 * side
        y = y2 - 2 * side
        for color in self._bit_colors():
            if not self._check_color(image, x, y, color):
                print("Incorrect color at x =", x)
                return False
            x -= side
        return True

    def valid(self, filename):
        return self.valid_image(Image.open(filename))

    def _draw_borders(self, draw, xsize, ysize):
        x1 = 0
        y1 = 0
        x2 = xsize
        y2 = ysize
        for brd in reversed(self._borders):
            draw.rectangle([x1, y1, x2, y2], fill=brd[4])
            x1 += brd[3]
            y1 += brd[0]
            x2 -= brd[1]
            y2 -= brd[2]
        return x1, y1, x2, y2

    def _draw_mark(self, draw, x1, y1, x2, y2):
        side = _IMAGE_SQUARE_SIDE
        draw.rectangle([x1, y1, x2, y2], fill="white")

        if self._use_color:
            corner_color = "black"
        else:
            corner_color = 128
        draw.rectangle([x1, y1, x1 + side, y1 + side], fill=corner_color)
        draw.rectangle([x1, y2 - side, x1 + side, y2], fill=corner_color)
        draw.rectangle([x2 - side, y1, x2, y1 + side], fill=corner_color)
        draw.rectangle([x2 - side, y2 - side, x2, y2], fill=corner_color)

        x = x2 - 2 * side
        y = y2 - 2 * side
        for bit_color in self._bit_colors():
            draw.rectangle([x, y, x + side, y + side], fill=bit_color)
            x -= side

    def _image_size_with_borders(self, borders):
        xsize = (borders[1] + borders[3] +
                 (_IMAGE_BIT_COUNT + 2) * _IMAGE_SQUARE_SIDE)
        ysize = borders[0] + borders[2] + _IMAGE_SQUARE_SIDE * 3
        return xsize, ysize

    def _total_borders(self, is_processed):
        res = [0, 0, 0, 0]
        if is_processed:
            count = self._borders_count_to_check
        else:
            count = len(self._borders)
        for i in range(count):
            for j in range(4):
                res[j] += self._borders[i][j]
        return tuple(res)

    def _bit_colors(self):
        color0 = (0, 255, 0) if self._use_color else 255
        color1 = (0, 0, 255) if self._use_color else 0
        ind = self._index
        for _ in range(_IMAGE_BIT_COUNT):
            yield (color0 if ind % 2 == 0 else color1)
            ind = ind // 2

    def _check_color(self, image, x, y, color):
        side = _IMAGE_SQUARE_SIDE
        count = side * side
        if self._use_color:
            tr = 0
            tg = 0
            tb = 0
            for i in range(side):
                for j in range(side):
                    r, g, b = image.getpixel((x + i, y + j))
                    tr += r
                    tg += g
                    tb += b
            real_color = (tr / count, tg / count, tb / count)
            for a, b in zip(color, real_color):
                if abs(a - b) > 35:
                    print("Color mismatch: real =", real_color,
                          "expected =", color)
                    return False
            return True
        else:
            t = 0
            for i in range(side):
                for j in range(side):
                    t += image.getpixel((x + i, y + j))
            real_color = t / count
            if abs(color - real_color) > 35:
                print("Color mismatch: real =", real_color,
                      "expected =", color)
                return False
            else:
                return True


class OutputChecker:
    """Abstract helper class that parses generated output of lnc."""

    def __init__(self, path):
        """Create checker for project located at path."""
        output_dir = self._create_dir_with_images(path)
        self._output_files = sorted(output_dir.listdir())

    def image_count(self):
        """Return total image count in the resulting sequence."""
        return len(self._output_files)

    def valid_image_at_index(self, index, reference_image):
        """Checks that image at given index is valid. Returns boolean."""
        filename = str(self._output_files[index])
        return reference_image.valid(filename)

    def valid_toc(self, toc):
        pass

    def _create_dir_with_images(self, path):
        """Create directory with page sequence 0000.png, 0001.png, ..."""
        pass


class PreparedImagesOutputChecker(OutputChecker):
    def _create_dir_with_images(self, path):
        # The directory already exists
        return path.join("cache").join("pages")

    def valid_toc(self, toc):
        # Nothing to check
        return True


class DocumentOutputChecker(OutputChecker):
    def __init__(self, path):
        self._doc = path.join("output").join("output." + self._extension())
        OutputChecker.__init__(self, path)

    def _create_dir_with_images(self, path):
        output_dir = path.join("temp_for_" + self._extension())
        output_dir.ensure(dir=True)
        subprocess.call([
            "convert",
            str(self._doc),
            "-alpha", "off",
            str(output_dir.join("%04d.png"))])
        return output_dir

    def _extension(self):
        """Return output file extension."""
        pass


class PDFDocumentChecker(DocumentOutputChecker):
    def _extension(self):
        return "pdf"

    def valid_toc(self, toc):
        with open(str(self._doc), "rb") as pdffile:
            parser = PDFParser(pdffile)
            document = PDFDocument(parser)
            try:
                real_toc = list(document.get_outlines())
            except PDFNoOutlines:
                return len(toc) == 0
            print("TOC from PDF file:", real_toc)
            if len(real_toc) != len(toc):
                print("Incorrect TOC length")
                return False
            for ref, real in zip(toc, real_toc):
                print("Checking", ref)
                if not ref[0] + 1 == real[0]:
                    # level
                    return False
                if not self._is_reference_to_ith_page(real[2][0], ref[1] - 1):
                    # destination
                    return False
                if not ref[2] == real[1]:
                    # title
                    return False
        return True

    def _is_reference_to_ith_page(self, reference, i):
        page = reference.resolve()
        page_refs = page['Parent'].resolve()['Kids']
        return page_refs[i].resolve() == page


class DjVuDocumentChecker(DocumentOutputChecker):
    def _extension(self):
        return "djvu"

    def valid_toc(self, toc):
        raw_toc = subprocess.check_output([
            "djvused",
            str(self._doc),
            "-e",
            "print-outline"])

        if raw_toc.strip() == "":
            return len(toc) == 0

        tokens = self._tokenize_raw_toc(raw_toc)
        real_toc = self._parse_toc(tokens)
        print("expected toc:", toc)
        print("real toc:", real_toc)
        if len(toc) != len(real_toc):
            return False
        for a, b in zip(toc, real_toc):
            print("Checking", a)
            if a != b:
                return False
        return True

    def _tokenize_raw_toc(self, data):
        """Tokenize output of djvused (some subset of what is described in the man page).

        Returns list of pairs (type, value) where type is one of the following:
        "(", ")" -- parentheses
        "str" -- string
        "sym" -- symbol
        """
        ind = 0
        length = len(data)
        res = []
        while ind < length:
            # ind points at the beginning of token or at whitespace in between
            while ind < length and data[ind] in " \t\r\n":
                ind += 1
            if ind >= length:
                break

            # Now ind points at the beginning of some token
            if data[ind] in "()":
                # parentheses
                res.append((data[ind], None))
                ind += 1
            elif data[ind].isalpha() or data[ind] in "_#":
                # symbol
                j = ind + 1
                while j < length and (data[j].isalnum() or data[j] in "_-#"):
                    j += 1
                res.append(("sym", data[ind:j]))
                ind = j
            else:
                # string
                assert data[ind] == "\""
                s = str()
                ind += 1
                while data[ind] != "\"":
                    if data[ind] == "\\":
                        if data[ind + 1] == "n":
                            s += "\n"
                            ind += 2
                        elif data[ind + 1] == "\\":
                            s += "\\"
                            ind += 2
                        elif data[ind + 1] == "\"":
                            s += "\""
                            ind += 2
                        elif data[ind + 1].isdigit():
                            j = ind + 1
                            while j < ind + 4 and data[j].isdigit():
                                j += 1
                            s += chr(int(data[ind+1:j], 8))
                            ind = j
                        else:
                            assert False
                    else:
                        s += data[ind]
                        ind += 1
                ind += 1  # skip \"
                res.append(("str", s.decode("utf8")))
        return res

    def _parse_toc(self, tokens):
        assert tokens[0] == ("(", None)
        assert tokens[1] == ("sym", "bookmarks")
        assert tokens[2] == ("(", None)
        depth = 0
        descr = None
        page = None
        res = []
        for tok in tokens[3:]:
            if tok[0] == "str":
                if descr is None:
                    descr = tok[1]
                elif page is None:
                    page = int(tok[1][1:])
                    res.append([depth, page, descr])
                else:
                    assert False
            elif tok[0] == "(":
                descr = page = None
                depth += 1
            elif tok[0] == ")":
                depth -= 1
            else:
                assert False
        return res
