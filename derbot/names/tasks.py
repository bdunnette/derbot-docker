import os
import random
from io import BytesIO

from celery import shared_task
from django.conf import settings
from django.core.files import File
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from derbot.names.models import DerbyName, Jersey
from derbot.names.utils import hex_to_rgb, text_wrap

# from unicodedata import name


logger = settings.LOGGER


@shared_task
def generate_tank(name_id, overwrite=False):
    try:
        name = DerbyName.objects.get(pk=name_id)
        if name.jersey and not overwrite:
            logger.info(
                f"{name.name} already has a tank and overwrite is set to {overwrite} - skipping"
            )
            return
        else:
            image_dir = settings.APPS_DIR.joinpath("names", "images")
            if name.jersey:
                jersey = name.jersey
            else:
                jersey = Jersey()
            logger.info(f"Generating tank for {name}")
            # open template image
            mask = Image.open(image_dir.joinpath("tank-mask.png"))
            logger.debug(f"Opened tank mask from {mask.filename}")
            fg_color = hex_to_rgb(jersey.fg_color)
            bg_color = hex_to_rgb(jersey.bg_color)
            number = str(name.number)
            # create grayscale version so we can re-color it
            im_gray = ImageOps.grayscale(mask)
            # colorize the jersey with our chosen name's "background" color
            im_color = ImageOps.colorize(im_gray, bg_color, "white")
            max_width = im_color.width * 0.6
            draw = ImageDraw.Draw(im_color)
            # choose random font
            font = random.choice(settings.FONTS)
            jersey.meta["font"] = font
            logger.info(f"Using {font} for {name.name}")
            font_path = os.path.join(settings.FONT_DIR, font)
            logger.info(f"Loading font from {font_path}")
            fnt1 = ImageFont.truetype(font_path, size=settings.TEXT_FONT_SIZE)
            # get size of name in our chosen font
            w, h = draw.textsize(name.name, font=fnt1)
            # break up name into multiple lines if necessary to fit on shirt
            lines = text_wrap(name.name, fnt1, max_width)
            logger.info(f"{name.name} will be printed on {len(lines)} lines: {lines}")
            # start to place name on shirt image - with current template, starting 20% down from top works well
            y = (im_color.height - h) * 0.3
            jersey.meta["name"] = {"font_size": fnt1.size, "y": y}
            logger.info(f"Starting to place name on image at y={y}")
            for line in lines:
                # add each line of name text to the image, centered
                line_width, line_height = draw.textsize(line, font=fnt1)
                logger.debug(
                    f"{line} will be printed at x={(im_color.width - line_width) / 2} y={y}"
                )
                draw.text(
                    ((im_color.width - line_width) / 2, y),
                    line,
                    fill=fg_color,
                    font=fnt1,
                )
                y += line_height
            if number:
                # create jersey number text
                nfs = settings.NUMBER_FONT_SIZE
                fnt2 = ImageFont.truetype(font_path, size=nfs)
                logger.debug(f"Writing number at {fnt2.size}pt")
                w, h = draw.textsize(number, font=fnt2)
                logger.debug(f"{number} text at {fnt2.size} is {w}x{h} px")
                # keep reducing size of number text until it's less than MAX_NUMBER_WIDTH
                while w > max_width:
                    nfs = nfs - 10
                    fnt2 = ImageFont.truetype(font_path, size=nfs)
                    w, h = draw.textsize(number, font=fnt2)
                # once number text will fit on shirt, add it to the image
                logger.debug(f"{number} text resized to {w}x{h} px")
                draw.text(
                    ((im_color.width - w) / 2, y), number, fill=fg_color, font=fnt2
                )
                jersey.meta["number"] = {
                    "font_size": fnt2.size,
                    "width": w,
                    "height": h,
                }
            # add overlay
            logger.info("Loading overlay")
            im_overlay = Image.open(image_dir.joinpath("tank-overlay.png"))
            logger.info("Adding overlay to image")
            im_final = ImageChops.multiply(im_color, im_overlay)
            # save generated image to the related name instance
            logger.info(f"Saving image to {name.name}")
            blob = BytesIO()
            im_final.save(blob, "JPEG")
            jersey.image.save("{}.jpg".format(name.id), File(blob), save=True)
            logger.info(f"Saved image to {jersey.image.name}")
            logger.info(dir(jersey))
            # save the tank to the database
            name.jersey = jersey
            name.save()
            return jersey.image.url
    except Exception as error:
        logger.error(f"Error generating tank for {name}: {error}")
