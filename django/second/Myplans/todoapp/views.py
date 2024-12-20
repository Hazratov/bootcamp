from rest_framework.viewsets import ModelViewSet

from todoapp.models import Todo
from todoapp.serializers import TodoSerializers

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class TodoViewSet(ModelViewSet):
    
    serializer_class = TodoSerializers
    authentication_classes  = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.validated_data["user"] = self.request.user
        serializer.save()