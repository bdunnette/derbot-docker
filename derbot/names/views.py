import logging

from django.shortcuts import get_object_or_404, redirect, render

from .models import DerbyName, Jersey

logger = logging.getLogger(__name__)


def jerseys(request):
    random_jerseys = Jersey.objects.order_by("?")[:42]
    context = {"jerseys": random_jerseys}
    return render(request, "names/jerseys.html", context)


def names_to_clear(request):
    uncleared_names = (
        DerbyName.objects.filter(cleared=False)
        .exclude(registered=True)
        .order_by("created")[:12]
    )
    context = {"names": uncleared_names}
    return render(request, "names/names_to_clear.html", context)


def approve_name(request, name_id):
    logger.info("Approving name %s", name_id)
    logger.debug(request)
    name = get_object_or_404(DerbyName, pk=name_id)
    name.cleared = True
    name.save()
    return redirect("names_to_clear")


def archive_name(request, name_id):
    logger.info("Archiving name %s", name_id)
    logger.debug(request)
    name = get_object_or_404(DerbyName, pk=name_id)
    name.archived = True
    name.save()
    return redirect("names_to_clear")
