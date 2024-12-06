import email
from email.policy import default
from wsgiref import validate
from .models import Issue, User, Project
from rest_framework import serializers
from .constants import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        try:
            user = User(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
            )
            user.set_password(validated_data['password'])
            user.save()
            return user
        except Exception as e:
            print(e)
    
    def update(self, user_instance, validated_data):
        try:
            user_instance.username = validated_data.get('username', user_instance.username)
            user_instance.email = validated_data.get('email', user_instance.email)
            user_instance.set_password(validated_data.get('password', user_instance.password))
            user_instance.save()
        except Exception as e:
            print(e)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "description"]
        read_only_fields = ['owner']

    def validate_title(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Title is too short. Must have 10 or above charectors")
        return value
        
    def validate_description(self, value):
        if len(value) < 20:
            raise serializers.ValidationError("Description is too short. Must have 20 or above charectors")
        return value

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'

class IssueRequestValidator(serializers.Serializer):
    sort_key = serializers.CharField(default='updated_at')
    sort_value = serializers.CharField(default=DESCENDING_ORDER)
    title = serializers.ListField(default=None)
    description = serializers.ListField(default=None)

    def validate_sort_key(self, value):
        if value not in ['title', 'description', 'created_at', 'updated_at']:
            print(f'issue serializer sort key is not valid - {value}')
        
        return value

    def validate_sort_value(self, value):
        if value not in [DESCENDING_ORDER, ASCENDING_ORDER]:
            print(f'issue serializer sort value is not valid - {value}')

        return value
