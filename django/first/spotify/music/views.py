from rest_framework.views import APIView
from rest_framework.response import Response

from music.serializers import SongSerializer
from music.models import Song

class SongAPIView(APIView):
    def get(self, request):
        Songs = Song.objects.all()
        Serializers = SongSerializer(Songs, many=True)

        return Response(Serializers.data)
    

    def post(self, request):
        serializer = SongSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(data=serializer.data)
