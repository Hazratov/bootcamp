from django.urls import path, include

from todoapp.views import TodoViewSet

from rest_framework.routers import DefaultRouter

todo_router = DefaultRouter()

todo_router.register("todo",TodoViewSet)

urlpatterns = [
    path("", include(todo_router.urls))
]