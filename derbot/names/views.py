from django.shortcuts import render

from .models import Jersey

# from rest_framework import permissions, viewsets
# from django.contrib.auth.models import Group, User
# from .serializers import GroupSerializer, UserSerializer


def jerseys(request):
    random_jerseys = Jersey.objects.order_by("?")[:18]
    context = {"jerseys": random_jerseys}
    return render(request, "names/jerseys.html", context)


# class UserViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows users to be viewed or edited.
#     """

#     queryset = User.objects.all().order_by("-date_joined")
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]


# class GroupViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows groups to be viewed or edited.
#     """

#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     permission_classes = [permissions.IsAuthenticated]
