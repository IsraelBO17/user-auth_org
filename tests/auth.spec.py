from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from hng.models import Organisation

from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User



##################################------- UNIT TESTS -------#################################

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User, Organisation
from datetime import timedelta
from django.utils import timezone
import uuid


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username=uuid.uuid4(),
            firstName='User1',
            lastName='Test',
            email='user1@example.com',
            password='testpassword'
        )
        self.user2 = User.objects.create_user(
            username=uuid.uuid4(),
            firstName='User2',
            lastName='Test',
            email='user2@example.com',
            password='testpassword'
        )
        self.organisation = Organisation.objects.create(name="User1's Organisation")
        self.organisation.users.add(self.user1)
        self.login_url = reverse('login')

    # Token Generation Test
    def test_token_generation(self):
        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)

        self.assertTrue(
            refresh.access_token.payload['exp'] > timezone.now().timestamp())
        self.assertEqual(
            refresh.access_token.payload['user_id'], self.user1.id)

    # Organisation Access Test
    def test_organisation_access(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(
            reverse('organisation_detail', kwargs={'pk': self.organisation.orgId}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertEqual(
            response.data['message'], "Organisation not found or you do not have access to this organisation")

    # Organisation Access Test for Authenticated User
    def test_organisation_access_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            reverse('organisation_detail', kwargs={'pk': self.organisation.orgId}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['name'], "User1's Organisation")

##################################------- END TO END TESTS -------#################################
class TestAuth(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        return super().setUp()

    def test_register_user_no_organisation(self):
        data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "johndoe@example.com",
            "password": "P@ssw0rd!",
            "phone": "+1234567890"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, 201)

        # Verify default organisation name is correctly generated
        user = User.objects.get(email=data['email'])
        expected_org_name = f"{data['firstName']}'s Organisation"
        organisation = Organisation.objects.get(name=expected_org_name)
        self.assertIn(user, organisation.users.all())

        # Check response contains expected user details and access token
        self.assertIn('data', response.data)
        self.assertIn('accessToken', response.data['data'].keys())

    def test_login_successful(self):
        data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "janesmith@example.com",
            "password": "SecurePwd123",
            "phone": "+1987654321"
        }
        login_data = {
            'email': 'janesmith@example.com',
            'password': 'SecurePwd123'
        }
        register_response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(register_response.status_code, 201)
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('accessToken', response.data['data'])

    def test_missing_required_fields(self):
        # Test cases for missing required fields during registration
        invalid_data_sets = [
            {"lastName": "Doe", "email": "johndoe@example.com",
                "password": "P@ssw0rd!"},
            {"firstName": "John", "email": "johndoe@example.com",
                "password": "P@ssw0rd!"},
            {"firstName": "John", "lastName": "Doe", "password": "P@ssw0rd!"},
            {"firstName": "John", "lastName": "Doe",
                "email": "johndoe@example.com"},
        ]
        for data in invalid_data_sets:
            response = self.client.post(self.register_url, data, format='json')
            # Assuming HTTP 422 Unprocessable Entity
            self.assertEqual(response.status_code, 400)
            self.assertIn('errors', response.data)

    def test_duplicate_email_or_username(self):
        # Test registration failure with duplicate email or username
        User.objects.create_user(
            username='existinguser', email='testuser@example.com', password='strongpassword123')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'anotherstrongpassword',
        }
        response = self.client.post(self.register_url, data, format='json')
        # Assuming HTTP 422 Unprocessable Entity
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)

    def tearDown(self):
        return super().tearDown()