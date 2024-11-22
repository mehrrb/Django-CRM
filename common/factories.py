import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from .models import Org, Profile, Document, APISettings, Address
from users.factories import UserFactory

class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Address
    
    address_line = factory.Faker('street_address')
    street = factory.Faker('street_name')
    city = factory.Faker('city')
    state = factory.Faker('state')
    postcode = factory.Faker('postcode')
    country = factory.Faker('country_code')

class OrgFactory(DjangoModelFactory):
    class Meta:
        model = Org
    
    name = factory.Sequence(lambda n: f'Test Organization {n}')
    address = factory.Faker('address')
    user = factory.SubFactory(UserFactory)
    country = factory.Faker('country')

class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile
    
    user = factory.SubFactory(UserFactory)
    org = factory.SubFactory(OrgFactory)
    role = FuzzyChoice(['ADMIN', 'MEMBER'])
    is_active = True

class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document
    
    title = factory.Sequence(lambda n: f'Test Document {n}')
    document_file = factory.django.FileField(filename='test.pdf')
    created_by = factory.SubFactory(ProfileFactory)
    status = FuzzyChoice(['active', 'inactive'])
    org = factory.SubFactory(OrgFactory)
    description = factory.Faker('paragraph')

class APISettingsFactory(DjangoModelFactory):
    class Meta:
        model = APISettings
    
    title = factory.Faker('sentence')
    website = factory.Faker('url')
    created_by = factory.SubFactory(ProfileFactory)
    org = factory.SubFactory(OrgFactory)