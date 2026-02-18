from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import factory
from faker import Faker
from .models import RegisterComplain, CrimeType, ComplainStatus, Case
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status


fake = Faker()
# Create your tests here.
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")

    full_name = factory.LazyAttribute(
        lambda x: f"{fake.first_name()} {fake.last_name()}"
    )

    national_id = factory.Sequence(lambda n: f"{1000000000 + n}")

    phone_number = factory.Sequence(lambda n: f"09{str(n).zfill(9)}")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "defaultpassword123"
        self.set_password(password)


class CanRegisterComplain(TestCase):
    def setUp(self):
        self.normal_group = Group.objects.get_or_create(name="Base User")[0]
        self.cadet_group = Group.objects.get_or_create(name="Cadet")[0]

        self.normal_user = UserFactory()
        self.normal_user.groups.add(self.normal_group)
        self.cadet_user = UserFactory()
        self.cadet_user.groups.add(self.normal_group)
        self.cadet_user.groups.add(self.cadet_group)
        self.client = APIClient()
        self.client2 = APIClient()

    def test_can_edit_case_first_time_model(self):
        complain = RegisterComplain.objects.create(
            creator=self.normal_user,
            title="some title",
            description="for test",
            incident_datetime=timezone.now(),
            incident_location="Test Location",
            crime_type=CrimeType.TYPE_1,
        )

        self.assertTrue(
            complain.can_be_edited_by_complainant(), "Can edit it at the first time!"
        )

    def test_can_make_using_endpoints(self):
        self.client.force_authenticate(user=self.normal_user)

        complaint_data = {
            "title": "API Test Complaint",
            "description": "This is a test complaint created via API",
            "incident_datetime": timezone.now().isoformat(),
            "incident_location": "API Test Location",
            "crime_type": CrimeType.TYPE_1,
        }
        response = self.client.post("/registercomplain/", complaint_data)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, "Unsuccessful request"
        )
        self.assertEqual(RegisterComplain.objects.count(), 1, "Not in database")

    def test_cannot_create_complaint_without_authentication(self):
        """Test that unauthenticated users cannot create complaints"""
        complaint_data = {
            "title": "Unauthorized",
            "description": "This should not be created",
            "incident_datetime": timezone.now(),
            "incident_location": "Test Location",
            "crime_type": CrimeType.TYPE_1,
        }

        response = self.client.post("/registercomplain/", complaint_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RegisterComplain.objects.count(), 0)

    def test_cannot_create_complaint_with_invalid_data(self):
        """Test that complaints cannot be created with invalid data"""
        self.client.force_authenticate(user=self.normal_user)

        invalid_data = {
            "title": "Incomplete Complaint",
        }

        response = self.client.post("/registercomplain/", invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_cadet_reject(self):
        self.client.force_authenticate(user=self.normal_user)

        complaint_data = {
            "title": "API Test Complaint",
            "description": "This is a test complaint created via API",
            "incident_datetime": timezone.now().isoformat(),
            "incident_location": "API Test Location",
            "crime_type": CrimeType.TYPE_1,
        }
        response = self.client.post("/registercomplain/", complaint_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        id1 = response.data["id"]
        response = self.client.post(f"/registercomplain/{id1}/submit/", {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cadet_review = {"action": "return", "message": "I like to do so"}
        self.client2.force_authenticate(user=self.cadet_user)
        response = self.client2.post(
            f"/registercomplain/{id1}/cadet_review/", cadet_review
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"/registercomplain/{id1}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["status"], ComplainStatus.RETURNED_TO_COMPLAINANT
        )


class CanRegisterComplainUsingEndpoints(TestCase):
    def setUp(self):
        self.normal_group = Group.objects.get_or_create(name="Base User")[0]
        self.cadet_group = Group.objects.get_or_create(name="Cadet")[0]
        self.police_group = Group.objects.get_or_create(name="Police Officer")[0]

        self.normal_user = UserFactory()
        self.normal_user.groups.add(self.normal_group)
        self.cadet_user = UserFactory()
        self.cadet_user.groups.add(self.normal_group)
        self.cadet_user.groups.add(self.cadet_group)

        self.police_user = UserFactory()
        self.police_user.groups.add(self.police_group)
        self.police_user.groups.add(self.normal_group)
        self.client = APIClient()
        self.client2 = APIClient()
        self.client3 = APIClient()
        self.complaint_data = {
            "title": "API Test Complaint",
            "description": "This is a test complaint created via API",
            "incident_datetime": timezone.now().isoformat(),
            "incident_location": "API Test Location",
            "crime_type": CrimeType.TYPE_1,
        }
        self.client.force_authenticate(user=self.normal_user)
        self.client2.force_authenticate(user=self.cadet_user)

    def test_can_register_ok_payload(self):
        response = self.client.post(
            "/registercomplain/", self.complaint_data, format="json"
        )
        id1 = response.data["id"]
        response = self.client.post(f"/registercomplain/{id1}/submit/", {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cadet_review = {"action": "accept", "message": "I like to do so"}
        response = self.client2.post(
            f"/registercomplain/{id1}/cadet_review/", cadet_review
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        officer_review = {"action": "accept", "message": "I like to do so"}
        self.client3.force_authenticate(user=self.police_user)
        res = self.client3.post(
            f"/registercomplain/{id1}/officer_review/", officer_review
        )
        # print(res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK, "officer can't accept")
        self.assertEqual(Case.objects.count(), 1, "Case hasn't created yet")

    def test_fail_because_of_3(self):
        response = self.client.post(
            "/registercomplain/", self.complaint_data, format="json"
        )
        id1 = response.data["id"]
        response = self.client.post(f"/registercomplain/{id1}/submit/", {})  # 1th time
        cadet_review = {"action": "return", "message": "I like to do so"}
        response = self.client2.post(
            f"/registercomplain/{id1}/cadet_review/", cadet_review
        )

        response = self.client.post(f"/registercomplain/{id1}/submit/", {})  # 2nd time
        response = self.client2.post(
            f"/registercomplain/{id1}/cadet_review/", cadet_review
        )

        self.assertEqual(
            response.data["status"],
            ComplainStatus.RETURNED_TO_COMPLAINANT,
            "Not returned to complaint",
        )

        response = self.client.post(f"/registercomplain/{id1}/submit/", {})  # 3th time
        response = self.client2.post(
            f"/registercomplain/{id1}/cadet_review/", cadet_review
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"/registercomplain/{id1}/")
        self.assertEqual(
            response.data["status"],
            ComplainStatus.CANCELLED,
            "Not canceled after 3 times",
        )


class CanReportScene(TestCase):
    def setUp(self):
        self.normal_group = Group.objects.get_or_create(name="Base User")[0]
        self.cadet_group = Group.objects.get_or_create(name="Cadet")[0]
        self.patrol = Group.objects.get_or_create(name="Patrol Officer")[0]

        self.normal_user = UserFactory()
        self.normal_user.groups.add(self.normal_group)
        self.cadet_user = UserFactory()
        self.cadet_user.groups.add(self.normal_group)
        self.cadet_user.groups.add(self.cadet_group)

        self.patrol_user = UserFactory()
        self.patrol_user.groups.add(self.patrol)
        self.patrol_user.groups.add(self.normal_group)
        self.client = APIClient()
        self.client2 = APIClient()
        self.client3 = APIClient()
        self.client3.force_authenticate(user=self.patrol_user)
        self.payload = {
            "occurred_at": "2026-02-18T13:55:52.406Z",
            "location": "string",
            "description": "Some random stuff",
            "crime_type": CrimeType.TYPE_3,
            "status": "DRAFT",
            "supervisor": 1,
        }

    def test_can_create_report(self):
        response = self.client3.post("/CrimeSceneReport/", self.payload)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
