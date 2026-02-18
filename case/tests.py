from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import factory
from faker import Faker
from .models import RegisterComplain,CrimeType
from datetime import timezone
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
        
        self.assertTrue(complain.can_be_edited_by_complainant(),"Can edit it at the first time!")
        
    def test_can_make_using_endpoints(self):
        self.client.force_authenticate(user=self.normal_user)
        
        complaint_data = {
            'title': 'API Test Complaint',
            'description': 'This is a test complaint created via API',
            'incident_datetime': timezone.now().isoformat(),
            'incident_location': 'API Test Location',
            'crime_type': CrimeType.TYPE_1,
        }
        create_url = reverse('register-complaint-list')
        response = self.client.post(create_url, complaint_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RegisterComplain.objects.count(), 1)
        
        complaint_id = response.data['id']
        
        detail_url = reverse('register-complaint-detail', args=[complaint_id])
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], complaint_data['title'])
        
        complaint = RegisterComplain.objects.get(id=complaint_id)
        self.assertEqual(complaint.creator, self.normal_user)
    
    def test_cannot_create_complaint_without_authentication(self):
        """Test that unauthenticated users cannot create complaints"""
        complaint_data = {
            'title': 'Unauthorized',
            'description': 'This should not be created',
            'incident_datetime': timezone.now().isoformat(),
            'incident_location': 'Test Location',
            'crime_type': CrimeType.TYPE_1,
        }
        
        create_url = reverse('register-complaint-list')
        response = self.client.post(create_url, complaint_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(RegisterComplain.objects.count(), 0)
        
    def test_cannot_create_complaint_with_invalid_data(self):
        """Test that complaints cannot be created with invalid data"""
        self.client.force_authenticate(user=self.normal_user)
        
        invalid_data = {
            'title': 'Incomplete Complaint',
        }
        
        create_url = reverse('register-complaint-list')
        response = self.client.post(create_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_can_cadet_reject(self):
        self.client.force_authenticate(user=self.normal_user)
        
        complaint_data = {
            'title': 'API Test Complaint',
            'description': 'This is a test complaint created via API',
            'incident_datetime': timezone.now().isoformat(),
            'incident_location': 'API Test Location',
            'crime_type': CrimeType.TYPE_1,
        }
        create_url = reverse('register-complaint-list')
        response = self.client.post(create_url, complaint_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.client2.force_authenticate(user=self.cadet_group)

class CanRegisterComplainUsingEndpoints(TestCase):
    def setUp(self):
        admin_data = {
            "username": "admin",
            "national_id": "0987654321",
            "full_name": "NaserAlDinShah",
            "phone_number": "09123456789",
            "email":"luke@dalton.com",
            "password": "prison"
        }
        self.client = APIClient()
        self.client.post("/register/",admin_data)
        self.admin_login = {
            "username": admin_data['username'],
            "password": admin_data['password']
        }
        
    def test_can_register_ok_payload(self):
        user_data = {
            "username": "lucky_luke",
            "national_id": "0987654321",
            "full_name": "Joe Dalton",
            "phone_number": "09123456789",
            "email":"luke@dalton.com",
            "password": "prison"
        }
        
        response = self.client.post("/register/",user_data)
        self.assertEqual(response.status_code,status.HTTP_201_CREATED,"OK")
        self.assertEqual(User.objects.count() , 1 , f"We have {User.objects.count()} user(s) in the database")