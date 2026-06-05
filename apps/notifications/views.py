from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            normalized = is_read.strip().lower()
            if normalized in {'true', '1', 'sim', 'yes'}:
                queryset = queryset.filter(is_read=True)
            elif normalized in {'false', '0', 'nao', 'no'}:
                queryset = queryset.filter(is_read=False)

        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)

        return queryset

    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        from django.utils import timezone
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-as-unread')
    def mark_as_unread(self, request, pk=None):
        notification = self.get_object()
        if notification.is_read:
            notification.is_read = False
            notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-all-as-unread')
    def mark_all_as_unread(self, request):
        updated = self.get_queryset().filter(is_read=True).update(is_read=False)
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

