from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload

# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ('url', 'username', 'email', 'groups')


# class GroupSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Group
#         fields = ('url', 'name')
        

class ValidateSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner')

class ValidateSerializer2(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner','result')

class ConvertSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ConvertFileUpload
        fields = ('created', 'file', 'owner','result','type')

class CompareSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = CompareFileUpload
        fields = ('created', 'file1','file2', 'owner','result')
