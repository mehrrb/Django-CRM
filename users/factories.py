import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from factory.fuzzy import FuzzyChoice

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('email',)  # Avoid duplicate users in tests
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.LazyAttribute(lambda obj: obj.email)  # Use email as username
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'password123')  # Default password
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for group in extracted:
                self.groups.add(group)

    @factory.post_generation
    def user_permissions(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for permission in extracted:
                self.user_permissions.add(permission)

class AdminUserFactory(UserFactory):
    """Factory for creating admin users"""
    is_staff = True
    is_superuser = True

class StaffUserFactory(UserFactory):
    """Factory for creating staff users"""
    is_staff = True