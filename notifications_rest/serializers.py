from rest_framework.serializers import ModelSerializer, RelatedField
from rest_framework import serializers
from notifications.models import Notification
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.timesince import timesince as timesince_

UserModel = get_user_model()


class UserSerializer(ModelSerializer):
    id = serializers.IntegerField()
    profile_picture = serializers.SerializerMethodField(method_name="get_profile_picture", required=False)

    def get_profile_picture(self, obj):
        # check if the CustomUser instance has a value for the profile_picture field
        if obj.profile_picture:
            print(obj.profile_picture)
            # return the value of the profile_picture field
            request = self.context.get("request")
            profile_picture_url = obj.profile_picture.url
            return request.build_absolute_uri(profile_picture_url)
        # return the default image if the CustomUser instance does not have a value for the profile_picture field
        else:
            return 'https://insurestag.plantsat.com/media/avatar.jpg'

    class Meta:
        model = UserModel
        fields = ['id', 'profile_picture']


class ContentTypeSerializer(ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['app_label', 'model']


class GenericNotificationRelatedField(RelatedField):

    def to_representation(self, value):
        if isinstance(value, UserModel):
            serializer = UserSerializer(value)
        if isinstance(value, ContentType):
            serializer = ContentTypeSerializer(value)

        return serializer.data


class NotificationSerializer(ModelSerializer):
    recipient = UserSerializer()
    actor = UserSerializer()
    verb = serializers.CharField()
    level = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField(read_only=True)
    unread = serializers.BooleanField()
    public = serializers.BooleanField()
    deleted = serializers.BooleanField()
    emailed = serializers.BooleanField()
    timesince = serializers.SerializerMethodField(read_only=True, method_name="get_timesince")

    def get_timesince(self, obj):
        return timesince_(obj.timestamp, None)

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'target', 'verb', 'level', 'description', 'unread', 'public', 'deleted',
                  'emailed', 'timestamp', 'timesince']

    def create(self, validated_data):
        recipient_data = validated_data.pop('recipient')
        recipient = UserModel.objects.get_or_create(id=recipient_data['id'])
        actor_data = validated_data.pop('actor')
        actor = UserModel.objects.get_or_create(id=actor_data['id'])
        notification = Notification.objects.create(recipient=recipient[0], actor=actor[0], **validated_data)
        return notification
