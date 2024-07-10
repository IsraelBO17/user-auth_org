import jwt
from datetime import timedelta, datetime, timezone

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone as datetime_zone

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from hng.models import Organisation

User = get_user_model()

class TokenGenerationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@mail.com',
            password='password123',
            firstName='test',
            lastName='user'
        )
        access_token = RefreshToken.for_user(self.user)
        self.decoded_token = jwt.decode(
            str(access_token.access_token), settings.SECRET_KEY, algorithms=['HS256']
        )

    def test_user_detail(self):
        userId = self.decoded_token.get('user_id')
        user = User.objects.get(userId=userId)

        self.assertEqual(user.email, 'testuser@mail.com')
    
    def test_token_expiration(self):
        exp = self.decoded_token.get('exp')
        expiry_datetime = datetime.utcfromtimestamp(exp)
        expected_expiry = self.utcnow() + timedelta(minutes=30)

        self.assertAlmostEqual(expiry_datetime, expected_expiry, delta=timedelta(seconds=5))
    
    @staticmethod
    def utcnow():
        return datetime_zone.now().utcnow()


class OrganisationAccessTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='testuser@mail.com', password='password123', firstName='test', lastName='user')
        self.organisation1 = Organisation.objects.create(name='Org1')
        self.organisation2 = Organisation.objects.create(name='Org2')
        self.user.organisation_set.add(self.organisation1)

        endpoint = '/auth/login'
        data = {'email': self.user.email, 'password': 'password123'}
        response = self.client.post(endpoint, data=data, format='json')
        user_token = response.data['data']['accessToken']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + user_token)

    def test_access_within_organisation(self):
        response = self.client.get(f'/api/organisations/{self.organisation1.orgId}')
        self.assertEqual(response.status_code, 200) 

    def test_access_outside_organisation(self):
        response = self.client.get(f'/api/organisations/{self.organisation2.orgId}')
        self.assertEqual(response.status_code, 403)


class RegisterEndpointTests(APITestCase):
    def test_successful_registration(self):
        url = '/auth/register'
        data = {
            'email':'testuser@mail.com',
            'password':'password123',
            'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        response = self.client.post(url, data, format='json')
        # Checks if the user is registered successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checks that the response contains the expected user details and access token
        self.assertIn('accessToken', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], 'testuser@mail.com')
        self.assertEqual(response.data['data']['user']['firstName'], 'test')
        self.assertEqual(response.data['data']['user']['lastName'], 'user')
        self.assertEqual(response.data['data']['user']['phone'], '+2348078675645')
        # Verify the default organization creation
        expected_org_name = "test's Organisation"
        user = User.objects.get(email='testuser@mail.com')
        organization = Organisation.objects.filter(users__in=[user]).first()
        self.assertEqual(organization.name, expected_org_name)
    
    def test_user_login(self):
        register_url = '/auth/register'
        register_data = {
            'email':'testuser@mail.com',
            'password':'password123',
            'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        register_response = self.client.post(register_url, register_data, format='json')

        url = '/auth/login'
        # Valid credentials
        data = {'email': 'testuser@mail.com', 'password': 'password123'}
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid credentials
        invalid_data = {'email': 'testuser@mail.com', 'password': 'password1234'}
        response = self.client.post(url, data=invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_email_missing(self):
        url = '/auth/register'
        data = {
            # 'email':'testuser@mail.com',
            'password':'password123',
            'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['errors'][0]['field'], 'email')
    
    def test_password_missing(self):
        url = '/auth/register'
        data = {
            'email':'testuser@mail.com',
            # 'password':'password123',
            'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['errors'][0]['field'], 'password')

    def test_firstName_missing(self):
        url = '/auth/register'
        data = {
            'email':'testuser@mail.com',
            'password':'password123',
            # 'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['errors'][0]['field'], 'firstName')
    
    def test_lastName_missing(self):
        url = '/auth/register'
        data = {
            'email':'testuser@mail.com',
            'password':'password123',
            'firstName':'test',
            # 'lastName':'user',
            'phone':'+2348078675645'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['errors'][0]['field'], 'lastName')
    
    def test_duplicate_user(self):
        url = '/auth/register'
        data = {
            'email':'testuser@mail.com',
            'password':'password123',
            'firstName':'test',
            'lastName':'user',
            'phone':'+2348078675645'
        }
        # Initial creation
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Duplicate creation
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


