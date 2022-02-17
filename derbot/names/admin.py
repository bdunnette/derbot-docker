from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext as _
from import_export.admin import ImportExportMixin

from derbot.names.models import DerbyName, DerbyNumber, Jersey, Toot
from derbot.names.tasks import generate_tank

logger = settings.LOGGER


class FavouritesFilter(admin.SimpleListFilter):
    title = _("Favourited")
    parameter_name = "faved"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(favourites_count__gt=0)
        if self.value() == "no":
            return queryset.filter(favourites_count=0)


class TootedFilter(admin.SimpleListFilter):
    title = _("Tooted")
    parameter_name = "tooted"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(~Q(tooted=None))
        if self.value() == "no":
            return queryset.filter(Q(tooted=None))


class JerseyFilter(admin.SimpleListFilter):
    title = _("has jersey")
    parameter_name = "has_jersey"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(~Q(jersey=None))
        if self.value() == "no":
            return queryset.filter(Q(jersey=None))


@admin.register(DerbyName)
class NameAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cleared",
        "registered",
        "archived",
        "created",
        "updated",
        "jersey",
    )
    list_filter = ["registered", "cleared", "archived", JerseyFilter]
    actions = ["clear", "unclear", "archive", "unarchive", "make_tanks"]

    @admin.action(description="Mark selected names as cleared for tooting")
    def clear(self, request, queryset):
        queryset.update(cleared=True)

    @admin.action(description="Mark selected names as NOT cleared for tooting")
    def unclear(self, request, queryset):
        queryset.update(cleared=False)

    @admin.action(description="Archive selected names")
    def archive(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Unrchive selected names")
    def unarchive(self, request, queryset):
        queryset.update(archived=False)

    @admin.action(description="Generate jerseys for selected names")
    def make_tanks(self, request, queryset):
        for name in queryset:
            print(name)
            logger.info(f"Generating tank for {name}")
            generate_tank.s(name.pk)


@admin.register(DerbyNumber)
class NumberAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "number", "created", "updated")
    list_filter = ["created", "updated"]


@admin.register(Jersey)
class JerseyAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "derbyname", "fg_color", "bg_color", "image")


@admin.register(Toot)
class TootAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "name", "toot_id", "date")
