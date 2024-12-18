from .views import HelloWorldAPIView
from django.urls import path

urlpatterns = [
    path('hello-world/', HelloWorldAPIView.as_view(), name="Hello world")
]
