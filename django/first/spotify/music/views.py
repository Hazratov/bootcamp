from rest_framework.views import APIView
from rest_framework.response import Response

from music.serializers import SongSerializer, AlbumSerializer, ArtistSerializer
from music.models import Song, Album, Artist

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from django.db import transaction
from rest_framework import filters

# class SongAPIView(APIView):
#     def get(self, request):
#         Songs = Song.objects.all()
#         Serializers = SongSerializer(Songs, many=True)

#         return Response(Serializers.data)

#     def post(self, request):
#         serializer = SongSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         serializer.save()

#         return Response(data=serializer.data)



class SongViewSet(ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ["listened", "-listened"]
    search_fields = ["title", "album__artist__name", "album__title"]

    @action(detail=True, methods=['POST'])
    def listen(self, request, *arg, **kwargs):
        song = self.get_object()
        with transaction.atomic():
            song.listened +=1
            song.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET'])
    def top(self, request, *arg, **kwargs):
        songs = self.get_queryset()
        songs = Song.objects.order_by('-listened')[:10]
        serializer = SongSerializer(songs, many=True)

        return Response(data=serializer.data)


class AlbumViewSet(ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer


class ArtistViewSet(ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer

    @action(detail=True, methods=["GET"])
    def albums(self, request, *arg, **kwargs):
        artist = self.get_object()
        serializer = AlbumSerializer(artist.album_set.all(), many=True)

        return Response(serializer.data)
