import os
import random
import string
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from celery import group, shared_task
from django.conf import settings
from django.core.files import File
from django.db.models import Exists, OuterRef, Q
from inscriptis import get_text
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from derbot.names.models import Color, DerbyName, DerbyNumber, Jersey, Toot
from derbot.names.utils import hex_to_rgb, text_wrap

logger = settings.LOGGER


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def pick_number(self, name_id):
    try:
        name = DerbyName.objects.get(id=name_id)
        new_number = DerbyNumber.objects.filter(Q(cleared=True)).order_by("?").first()
        if new_number:
            name.number = new_number
            name.save()
            return name.number.number
        else:
            return None
    except Exception as e:
        logger.error(f"Error picking number for {name_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_tank(self, name_id, overwrite=False):
    try:
        name = DerbyName.objects.get(pk=name_id)
        if name.jersey and not overwrite:
            logger.info(
                f"{name.name} already has a tank and overwrite is set to {overwrite} - skipping"
            )
            return
        else:
            if name.jersey:
                jersey = name.jersey
            else:
                jersey = Jersey()
                jersey.fg_color = Color.objects.order_by("?").first()
                jersey.bg_color = jersey.fg_color.pair_with
                jersey.save()
            number = str(name.number)
            logger.info(f"Generating tank for {name}, number {number}")
            # open template image
            image_dir = settings.APPS_DIR.joinpath("names", "images")
            logger.info(f"Loading template images from {image_dir}")
            mask = Image.open(image_dir.joinpath("tank-mask.png"))
            logger.info(f"Opened tank mask from {mask.filename}")
            fg_color = hex_to_rgb(jersey.fg_color.hex)
            bg_color = hex_to_rgb(jersey.bg_color.hex)
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
            if number is not None:
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
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_names_twoevils(
    self, session=settings.SESSION, timeout=settings.REQUEST_TIMEOUT
):
    try:
        url = "https://www.twoevils.org/rollergirls/"
        logger.info("Downloading names from %s" % url)
        r = session.get(url, timeout=timeout)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.find_all("tr", {"class": ["trc1", "trc2"]})
        names = [row.find("td").get_text() for row in rows]
        new_name_objs = [
            DerbyName(name=n, registered=True) for n in names if len(n) > 1
        ]
        DerbyName.objects.bulk_create(new_name_objs, ignore_conflicts=True)
    except Exception as error:
        logger.error(f"Error fetching names from {url}: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_names_drc(self, session=settings.SESSION, timeout=settings.REQUEST_TIMEOUT):
    try:
        url = "http://www.derbyrollcall.com/everyone"
        logger.info("Downloading names from %s" % url)
        r = session.get(url, timeout=timeout)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.find_all("td", {"class": "name"})
        names = [td.get_text() for td in rows]
        logger.info(f"Found {len(names)} names")
        new_name_objs = [
            DerbyName(name=n, registered=True) for n in names if len(n) > 1
        ]
        logger.info(f"Found {len(new_name_objs)} new names")
        DerbyName.objects.bulk_create(new_name_objs, ignore_conflicts=True)
    except Exception as error:
        logger.error(f"Error fetching names from {url}: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_names_wftda(self, session=settings.SESSION, timeout=settings.REQUEST_TIMEOUT):
    try:
        url = "https://resources.wftda.org/officiating/roller-derby-certification-program-for-officials/roster-of-certified-officials/"
        logger.info("Downloading names from {0}".format(url))
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        r = session.get(url, timeout=timeout)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.find_all("h5")
        names = [r.find("a").get_text() for r in rows]
        new_name_objs = [
            DerbyName(name=n, registered=True) for n in names if len(n) > 1
        ]
        DerbyName.objects.bulk_create(new_name_objs, ignore_conflicts=True)
    except Exception as error:
        logger.error(f"Error fetching names from {url}: {error}")
        raise self.retry(exc=error)


@shared_task(bind=True, autoretry_for=(Exception,))
def fetch_names_rdr(
    self,
    initial_letters=string.ascii_uppercase + string.digits + string.punctuation,
):
    try:
        result = group(fetch_names_rdr_letter.s(letter) for letter in initial_letters)
        result.apply_async()
    except Exception as error:
        logger.error(f"Error fetching names: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_names_rdr_letter(
    self, letter=None, session=settings.SESSION, timeout=settings.REQUEST_TIMEOUT
):
    try:
        if letter:
            try:
                names = []
                url = "https://rollerderbyroster.com/view-names/?ini={0}".format(letter)
                logger.info("Downloading names from {0}".format(url))
                r = session.get(url, timeout=timeout)
                soup = BeautifulSoup(r.text, "lxml")
                rows = soup.find_all("ul")
                # Use only last unordered list - this is where names are!
                for idx, li in enumerate(rows[-1]):
                    # Name should be the text of the link within the list item
                    name = li.find("a").get_text()
                    names.append(name)
                new_name_objs = [
                    DerbyName(name=n, registered=True) for n in names if len(n) > 1
                ]
                DerbyName.objects.bulk_create(new_name_objs, ignore_conflicts=True)
            except requests.Timeout:
                logger.warning("  Timeout reading from {0}".format(url))
                pass
        else:
            logger.warning("Need initial letter!")
            return False
    except Exception as error:
        logger.error(f"Error fetching names from {url}: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_colors(self, mastodon=settings.MASTO, color_bot=settings.COLOR_BOT):
    try:
        account_id = mastodon.account_search(color_bot)[0]["id"]
        statuses = mastodon.account_statuses(account_id, exclude_replies=True)
        while statuses:
            for s in statuses:
                if s.favourites_count > 0:
                    # Get first two items/lines from toot, since these contain colors
                    status_colors = get_text(s.content).strip().splitlines()[:2]
                    logger.info(f"Found colors: {status_colors}")
                    # Get last element of each line, containing color hex code
                    color_codes = [
                        {
                            "hex": c.split()[-1].lstrip("#"),
                            "name": " ".join(c.split()[:-1]).rstrip("#").strip(),
                        }
                        for c in status_colors
                    ]
                    logger.info(f"Color codes: {color_codes}")
                    color1 = color_codes[0]
                    c1, created = Color.objects.update_or_create(
                        name=color1["name"],
                        hex=color1["hex"],
                    )
                    color2 = color_codes[1]
                    c2, created = Color.objects.update_or_create(
                        name=color2["name"],
                        hex=color2["hex"],
                        pair_with=c1,
                    )
                    c1.pair_with = c2
                    c1.save()
            statuses = mastodon.fetch_next(statuses)
    except Exception as error:
        logger.error(f"Error fetching colors from {color_bot}: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def fetch_toots(self, mastodon=settings.MASTO):
    try:
        account_id = mastodon.account_verify_credentials()["id"]
        logger.info("Downloading statuses for account {0}...".format(account_id))
        statuses = mastodon.account_statuses(account_id, exclude_replies=True)
        while statuses:
            # logger.debug(statuses)
            # logger.debug(dir(statuses))
            new_name_objs = [
                DerbyName(
                    name=get_text(s.content).strip(),
                    toot_id=s.id,
                    tooted=s.created_at,
                    reblogs_count=s.reblogs_count,
                    favourites_count=s.favourites_count,
                )
                for s in statuses
            ]
            DerbyName.objects.bulk_create(new_name_objs, ignore_conflicts=True)
            statuses = mastodon.fetch_next(statuses)
    except Exception as error:
        logger.error(f"Error fetching toots: {error}")
        raise self.retry(exc=error)


@shared_task(
    bind=True,
    default_retry_delay=30,
    max_retries=3,
    soft_time_limit=60,
    retry_backoff=True,
    autoretry_for=(Exception,),
)
def toot_name(
    self,
    name_id=None,
    mastodon=settings.MASTO,
    min_wait=settings.MIN_WAIT,
    max_wait=settings.MAX_WAIT,
):
    try:
        if name_id:
            name = DerbyName.objects.get(pk=name_id)
        else:
            # Select a random name that is unregistered, cleared, has a jersey and has no toot
            name = (
                DerbyName.objects.filter(
                    Q(registered=False)
                    & Q(cleared=True)
                    & ~Q(jersey=False)
                    & ~Q(Exists(Toot.objects.filter(name=OuterRef("pk"))))
                )
                .order_by("?")
                .first()
            )
        logger.info(name)
        if name:
            if max_wait > 0:
                delay = random.randint(min_wait, max_wait)
                logger.info(
                    "Waiting {0} seconds before tooting {1}".format(delay, name)
                )
                toot_name.s(name.pk).apply_async(countdown=delay)
            else:
                logger.info("Tooting name '{0}'...".format(name))
                toot = None
                toot_content = " ".join(
                    [str(name)] + [str(t) for t in settings.TOOT_TAGS]
                )
                if bool(name.jersey):
                    image_description = "{0}-colored shirt with '{1}' and the number {2} printed on it in {3} lettering.".format(
                        str(name.jersey.bg_color.name),
                        str(name),
                        name.number,
                        str(name.jersey.fg_color.name),
                    )
                    logger.info(image_description)
                    media = mastodon.media_post(
                        name.jersey.image,
                        mime_type="image/jpeg",
                        description=image_description,
                    )
                    if settings.ACTUALLY_TOOT:
                        toot = mastodon.status_post(toot_content, media_ids=media)
                else:
                    if settings.ACTUALLY_TOOT:
                        toot = mastodon.status_post(toot_content)
                if toot:
                    logger.info("  Tooted at {0}".format(toot.created_at))
                    toot_obj = Toot(toot_id=toot.id, date=toot.created_at, name=name)
                    toot_obj.save()
                    return toot_obj.toot_id
                else:
                    return toot_content
        else:
            logger.info("No matching names found, exiting...")
            return None
    except Exception as error:
        logger.error(f"Error tooting name {name_id}: {error}")
        raise self.retry(exc=error)
