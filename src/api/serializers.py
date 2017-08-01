from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import ValidateFileUpload

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')
        

class FileUploadSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner')
