from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from derbot.names.models import DerbyName

from .serializers import NameSerializer


class NameViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = NameSerializer
    queryset = DerbyName.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("cleared", "registered", "archived")
    lookup_field = "id"
