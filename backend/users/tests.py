#backend/users/tests.py
from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status

# Create your tests here.
from django.contrib.auth import get_user_model


User = get_user_model()


class CanRegisterAndLogin(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_can_register_ok_payload(self):
        user_data = {
            "username": "lucky_luke",
            "national_id": "0987654321",
            "full_name": "Joe Dalton",
            "phone_number": "09123456789",
            "email": "luke@dalton.com",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")
        self.assertEqual(
            User.objects.count(),
            1,
            f"We have {User.objects.count()} user(s) in the database",
        )

    def test_cant_register_bad_payload(self):
        user_data = {
            "username": "lucky_luke",
            "national_id": "0987654321",
            "phone_number": "09123456789",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "OK")
        self.assertIn("email", response.data)

    def test_uniqueness_of_username(self):
        user_data1 = {
            "username": "lucky_luke2",
            "national_id": "0987654321",
            "full_name": "Joe Dalton",
            "phone_number": "09123456788",
            "email": "trump@dalton.com",
            "password": "prison",
        }

        user_data2 = {
            "username": "lucky_luke2",
            "national_id": "0987654322",
            "full_name": "Joe Biden",
            "phone_number": "09123456789",
            "email": "trump1@dalton.com",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")

        response = self.client.post("/register/", user_data2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "OK")
        self.assertIn("username", response.data)

    def test_can_login_after_register(self):
        user_data1 = {
            "username": "ShahAbbas1",
            "national_id": "0987634321",
            "full_name": "Shah Abbas Safavi",
            "phone_number": "09123456788",
            "email": "trump@dalton.com",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")
        user_data_login = {"username": "ShahAbbas1", "password": "prison"}

        self.assertEqual(User.objects.count(), 1, "Not  user in the database")
        self.assertEqual(
            User.objects.get(username="ShahAbbas1").national_id,
            "0987634321",
            "Very bad",
        )

        response = self.client.post("/login/", user_data_login)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ping_response = self.client.get("/register/ping/")

        self.assertEqual(ping_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ping_response.data["username"], "ShahAbbas1")
        self.assertEqual(ping_response.data["message"], "success")

    def test_cannot_login_with_bad_payload(self):
        user_data1 = {
            "username": "ShahAbbas1",
            "national_id": "0987634321",
            "full_name": "Shah Abbas Safavi",
            "phone_number": "09123456788",
            "email": "trump@dalton.com",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")

        user_data_login = {"username": "ShahAbbas1", "password": "prisoner"}

        response = self.client.post("/login/", user_data_login)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_assign_role(self):
        admin_data = {
            "username": "admin",
            "national_id": "0987654334",
            "full_name": "Joe Dalton",
            "phone_number": "09123446789",
            "email": "lukxxxe@dalton.com",
            "password": "prison",
        }
        response = self.client.post("/register/", admin_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")

        user_data = {
            "username": "user",
            "national_id": "0987654398",
            "full_name": "Joe Dalton",
            "phone_number": "09123146329",
            "email": "lukxdsxxe@dalton.com",
            "password": "prison",
        }

        response = self.client.post("/register/", user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "OK")
        admin_login = {
            "national_id": admin_data["national_id"],
            "password": admin_data["password"],
        }
        response = self.client.post("/login/", admin_login)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "OK")
        grant_data = {"role": "Detective", "username": "user"}
        response = self.client.post("/register/grant_role/", grant_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_login = {
            "national_id": user_data["national_id"],
            "password": user_data["password"],
        }
        response = self.client.post("/login/", user_login)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        response = self.client.get('/register/role/')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertTrue("Detective" in response.data)

