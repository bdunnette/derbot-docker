from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from derbot.names.api.views import NameViewSet
from derbot.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("names", NameViewSet)

app_name = "api"
urlpatterns = router.urls
