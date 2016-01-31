from PIL import Image, ImageDraw


class ProjectBuilder:
    def __init__(self):
        self.images = []

    def create_image(self):
        image = TestImage()
        self.images.append(image)
        return image

    def run_test(self):
        self.save_images()
        self.save_TOC()
        self.save_config()
        self.run_program()
        self.check()

    def save_images(self):
        for image in self.images:
            image.save()

    def save_TOC(self):
        pass

    def save_config(self):
        pass

    def run_program(self):
        pass

    def check(self):
        pass


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


class TestImage:
    def __init__(self, index, use_color):
        self._index = index
        self._use_color = use_color
        self._borders = []
        self._borders_count_to_check = 0

    def add_border(self, up, right, down, left, color):
        self._borders.append((up, right, down, left, color))
        self._borders_count_to_check += 1
        return self

    def border_count_to_check(self, count):
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

    def save(self, filename):
        self.create_image().save(filename)

    def check_image(self, image):
        borders = self._total_borders(is_processed=True)
        xsize, ysize = self._image_size_with_borders(borders)
        real_xsize, real_ysize = image.size
        if ((self._use_color and image.mode != "RGB") or
            (not self._use_color and image.mode == "RGB")):
            return False
        if not (abs(xsize - real_xsize) < 10 and
                abs(ysize - real_ysize) < 10):
            return False

        side = _IMAGE_SQUARE_SIDE
        x1 = borders[3]
        y1 = borders[0]
        x2 = x1 + (_IMAGE_BIT_COUNT + 2) * side
        y2 = y1 + 3 * side
        edge_color = (0, 0, 0) if self._use_color else 128
        if not (self._check_color(image, x1, y1, edge_color) and
                self._check_color(image, x1, y2 - side, edge_color) and
                self._check_color(image, x2 - side, y1, edge_color) and
                self._check_color(image, x2 - side, y2 - side, edge_color)):
            return False

        x = x2 - 2 * side
        y = y2 - 2 * side
        for color in self._bit_colors():
            if not self._check_color(image, x, y, color):
                return False
            x -= side
        return True

    def check(self, filename):
        return self.check_image(Image.open(filename))

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
            edge_color = "black"
        else:
            edge_color = 128
        draw.rectangle([x1, y1, x1 + side, y1 + side], fill=edge_color)
        draw.rectangle([x1, y2 - side, x1 + side, y2], fill=edge_color)
        draw.rectangle([x2 - side, y1, x2, y1 + side], fill=edge_color)
        draw.rectangle([x2 - side, y2 - side, x2, y2], fill=edge_color)

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
            for a, b in zip(color, (tr / count, tg / count, tb / count)):
                if abs(a - b) > 10:
                    return False
            return True
        else:
            t = 0
            for i in range(side):
                for j in range(side):
                    t += image.getpixel((x + i, y + j))
            return abs(color - t / count) <= 10


class OutputChecker:
    def __init__(self, filename):
        pass

    def check(self, projectBuilder):
        current = 0
        for image in projectBuilder.images:
            if image.forOutput:
                image.check(self.get_image_at_index(current))
                current += 1
        self.check_TOC(projectBuilder.toc)

    def get_image_at_index(self):
        pass

    def check_TOC(self, toc):
        pass
