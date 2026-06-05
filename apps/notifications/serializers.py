from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id_notification', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'type',
            'title',
            'message',
            'is_read',
            'created_at',
            'read_at',
            'related_id',
        ]
        read_only_fields = fields
