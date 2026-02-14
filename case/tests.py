from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import factory
from faker import Faker
fake = Faker()
# Create your tests here.
User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    
    full_name = factory.LazyAttribute(lambda x: f"{fake.first_name()} {fake.last_name()}")
    
    national_id = factory.Sequence(lambda n: f"{1000000000 + n}") 
    
    phone_number = factory.Sequence(lambda n: f"09{str(n).zfill(9)}")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "defaultpassword123"
        self.set_password(password)


class CanRegisterComplain(TestCase):
    def setUp(self):
        # self.normal_group = Group.objects.get_or_create('Base User')
        # self.cadet_group = Group.objects.get_or_create('Cadet')
        
        # self.normal_user = UserFactory()
        # self.normal_user.groups.add(self.normal_group)
        return super().setUp()
    
    def test_new_case(self):
        self.assertEqual(1,2,"1 == 1")
