from django.conf import settings
from django.contrib import admin
from django.db import IntegrityError
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext as _
from import_export import resources
from import_export.admin import ImportExportMixin, ImportExportModelAdmin

from derbot.names.models import Color, DerbyName, DerbyNumber, Jersey, Toot
from derbot.names.tasks import generate_tank, pick_number, toot_name

logger = settings.LOGGER


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
            return queryset.filter(Q(Exists(Toot.objects.filter(name=OuterRef("pk")))))
        if self.value() == "no":
            return queryset.filter(~Q(Exists(Toot.objects.filter(name=OuterRef("pk")))))


class JerseyFilter(admin.SimpleListFilter):
    title = _("has jersey")
    parameter_name = "jersey"

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


class NameResource(resources.ModelResource):
    class Meta:
        model = DerbyName
        skip_unchanged = True
        report_skipped = True
        # use_bulk = True
        # batch_size = 100

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super(NameResource, self).save_instance(
                instance, using_transactions, dry_run
            )
        except IntegrityError:
            pass


class NumberResource(resources.ModelResource):
    class Meta:
        model = DerbyNumber
        skip_unchanged = True
        report_skipped = True
        # use_bulk = True
        # batch_size = 100

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        try:
            super(NumberResource, self).save_instance(
                instance, using_transactions, dry_run
            )
        except IntegrityError:
            pass


@admin.register(DerbyName)
class NameAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "name",
        "number",
        "cleared",
        "registered",
        "archived",
        "created",
        "updated",
        "jersey",
    )
    list_filter = ["registered", "cleared", "archived", JerseyFilter, TootedFilter]
    actions = [
        "clear",
        "unclear",
        "archive",
        "unarchive",
        "new_numbers",
        "make_tanks",
        "toot",
    ]
    resource_class = NameResource

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

    @admin.action(description="Choose (new) numbers for selected names")
    def new_numbers(self, request, queryset):
        for name in queryset:
            print(name)
            logger.info(f"Picking new number for {name}")
            pick_number.delay(name.pk)
        self.message_user(request, "New numbers chosen for selected names")

    @admin.action(description="Generate tanks for selected names")
    def make_tanks(self, request, queryset):
        for name in queryset:
            print(name)
            logger.info(f"Generating tank for {name}")
            generate_tank.delay(name.pk, overwrite=True)

    @admin.action(description="Toot selected names")
    def toot(self, request, queryset):
        logger.info(f"Tooting {queryset.count()} names")
        for name in queryset:
            logger.info(f"Tooting {name}")
            toot_name.delay(name.pk, max_wait=0)


@admin.register(DerbyNumber)
class NumberAdmin(ImportExportModelAdmin):
    list_display = ("id", "number", "created", "updated")
    list_filter = ["created", "updated"]
    resource_class = NumberResource


@admin.register(Jersey)
class JerseyAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "derbyname", "fg_color", "bg_color", "image")


@admin.register(Toot)
class TootAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "name", "toot_id", "date")


@admin.register(Color)
class ColorAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("id", "name", "hex", "pair_with")
