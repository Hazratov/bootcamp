from django.urls import path, include

from todoapp.views import TodoViewSet

from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

todo_router = DefaultRouter()

todo_router.register("todo", TodoViewSet, "todo")

urlpatterns = [
    path("", include(todo_router.urls)),
    path("auth/", obtain_auth_token)
]