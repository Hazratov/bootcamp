from rest_framework.viewsets import ModelViewSet

from todoapp.models import Todo
from todoapp.serializers import TodoSerializers

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class TodoViewSet(ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializers
    authentication_classes  = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
