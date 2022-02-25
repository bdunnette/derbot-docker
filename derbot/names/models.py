from colorfield.fields import ColorField
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from model_utils import FieldTracker

from .utils import hex_to_rgb

logger = settings.LOGGER


class DerbyName(models.Model):
    name = models.CharField(max_length=255, unique=True)
    number = models.ForeignKey(
        "DerbyNumber", on_delete=models.SET_NULL, blank=True, null=True
    )
    jersey = models.OneToOneField(
        "Jersey", on_delete=models.CASCADE, null=True, blank=True
    )
    registered = models.BooleanField(default=False)
    cleared = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    meta = models.JSONField(default=dict, null=True, blank=True)
    number_tracker = FieldTracker(fields=["number"])

    def __str__(self):
        return self.name


class DerbyNumber(models.Model):
    number = models.CharField(max_length=64, unique=True)
    cleared = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    meta = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return self.number


class Color(models.Model):
    name = models.CharField(max_length=64)
    hex = ColorField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    pair_with = models.ForeignKey(
        "Color", on_delete=models.SET_NULL, null=True, blank=True
    )
    meta = models.JSONField(default=dict, null=True, blank=True)

    class Meta:
        unique_together = ("hex", "pair_with")

    def __str__(self):
        return f"{self.name} ({self.hex})"

    def rgb(self):
        return hex_to_rgb(self.hex)


class Toot(models.Model):
    name = models.ForeignKey(
        "DerbyName", on_delete=models.SET_NULL, null=True, blank=True
    )
    toot_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    date = models.DateTimeField(default=None, null=True, blank=True)
    reblogs_count = models.IntegerField(default=0)
    favourites_count = models.IntegerField(default=0)
    meta = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return f"{self.toot_id}: {self.name}"


class Jersey(models.Model):
    fg_color = models.ForeignKey(
        "Color", on_delete=models.SET_NULL, null=True, related_name="fg_color"
    )
    bg_color = models.ForeignKey(
        "Color", on_delete=models.SET_NULL, null=True, related_name="bg_color"
    )
    image = models.ImageField(
        upload_to="jerseys/", storage=default_storage, null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    meta = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        if self.derbyname:
            return f"{self.derbyname}"
        else:
            return f"{self.fg_color} {self.bg_color}"
