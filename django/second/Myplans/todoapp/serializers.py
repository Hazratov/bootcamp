from rest_framework import serializers

from .models import Todo


class TodoSerializers(serializers.ModelSerializer):
    model = Todo
    fields = ('title', 'description', 'status')
