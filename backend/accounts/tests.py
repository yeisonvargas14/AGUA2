from django.test import TestCase
from django.urls import reverse
from accounts.models import User

class AccountTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client1',
            email='client1@example.com',
            password='testpassword123',
            role=User.Roles.CLIENT
        )
        self.driver_user = User.objects.create_user(
            username='driver1',
            email='driver1@example.com',
            password='testpassword123',
            role=User.Roles.DRIVER
        )
        self.admin_user = User.objects.create_superuser(
            username='admin1',
            email='admin1@example.com',
            password='testpassword123',
            role=User.Roles.ADMIN
        )

    def test_user_creation_with_roles(self):
        """Test that users are created with correct roles."""
        self.assertEqual(self.client_user.role, User.Roles.CLIENT)
        self.assertEqual(self.driver_user.role, User.Roles.DRIVER)
        self.assertEqual(self.admin_user.role, User.Roles.ADMIN)
        self.assertTrue(self.admin_user.is_superuser)

    def test_unauthenticated_user_redirect(self):
        """Unauthenticated user should be redirected to login when accessing dashboard."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_role_access_control(self):
        """Test that client cannot access admin dashboard."""
        self.client.login(username='client1', password='testpassword123')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect back to client dashboard with a permission message
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('client_dashboard'), response.url)
