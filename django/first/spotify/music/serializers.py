from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Song, Album, Artist



class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = "__all__"

class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = "__all__"

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ('id', 'title', 'album', 'cover', 'source')

    def validate_source(self, value):
        if not value.endswith(".mp3"):
            raise ValidationError(detail="The music is required .mp3")
        return value    
            
