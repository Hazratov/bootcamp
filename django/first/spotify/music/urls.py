from .views import SongAPIView
from django.urls import path

urlpatterns = [
    path('songs/', SongAPIView.as_view(), name="songs")
]
