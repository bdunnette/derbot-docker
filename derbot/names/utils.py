from django.conf import settings

logger = settings.LOGGER


def hex_to_rgb(hex):
    # From https://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa
    hex = hex.lstrip("#")
    rgb = tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))
    return rgb


def text_wrap(text, font, max_width):
    # From https://fiveminutes.today/articles/putting-text-on-images-with-python-pil/
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(" ")
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ""
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word,
            # add the line to the lines array
            lines.append(line.strip())
    return lines
