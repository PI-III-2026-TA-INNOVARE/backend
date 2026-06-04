from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.models import Notification
from apps.users.models import User


class NotificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='SenhaForte123',
            id_type=User.UserType.PESQUISADOR,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='SenhaForte123',
            id_type=User.UserType.EMPRESA,
        )
        self.notification = Notification.objects.create(
            user=self.user,
            type='status_alterado',
            title='Atualizacao',
            message='Status alterado.',
            related_id=10,
        )
        Notification.objects.create(
            user=self.other_user,
            type='status_alterado',
            title='Outra',
            message='Nao deve aparecer.',
        )
        self.client.force_authenticate(self.user)

    def test_list_returns_only_authenticated_user_notifications(self):
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.notification.id_notification)

    def test_unread_count_uses_authenticated_user_notifications(self):
        response = self.client.get('/api/notifications/unread-count/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)

    def test_mark_as_read(self):
        response = self.client.post(f'/api/notifications/{self.notification.id_notification}/mark-as-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_as_read(self):
        response = self.client.post('/api/notifications/mark-all-as-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated'], 1)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
