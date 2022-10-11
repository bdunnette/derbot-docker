from rest_framework import serializers

from derbot.names.models import DerbyName


class NameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DerbyName
        fields = (
            "id",
            "name",
            "registered",
            "cleared",
            "archived",
            "created",
            "updated",
        )
