import pytest
from common.utils import (
    is_document_file_audio,
    is_document_file_image,
    is_document_file_pdf,
    append_str_to,
    get_client_ip
)
from common.validators import (
    validate_organization_name,
    validate_file_extension,
    validate_phone_number
)
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestFileUtils:
    def test_file_type_detection(self):
        """Test file type detection utilities"""
        assert is_document_file_audio('mp3')
        assert is_document_file_image('jpg')
        assert is_document_file_pdf('pdf')
        assert not is_document_file_pdf('doc')

    def test_string_concatenation(self):
        """Test string concatenation utility"""
        result = append_str_to("Hello", "World", sep=" ")
        assert result == "Hello World"
        
        result = append_str_to("Test", "1", "2", "3", sep="-")
        assert result == "Test-1-2-3"

    def test_client_ip_detection(self):
        """Test client IP detection"""
        class MockRequest:
            META = {
                'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                'REMOTE_ADDR': '5.6.7.8'
            }
        
        request = MockRequest()
        ip = get_client_ip(request)
        assert ip == '1.2.3.4'

@pytest.mark.django_db
class TestValidators:
    def test_organization_name_validation(self):
        """Test organization name validation"""
        # Valid names
        validate_organization_name("Test Organization")
        validate_organization_name("Company123")
        
        # Invalid names
        with pytest.raises(ValidationError):
            validate_organization_name("Te")  # Too short
        with pytest.raises(ValidationError):
            validate_organization_name("Test@Org")  # Invalid characters

    def test_file_extension_validation(self):
        """Test file extension validation"""
        class MockFile:
            def __init__(self, name, size):
                self.name = name
                self.size = size

        # Test invalid extension
        invalid_file = MockFile("test.exe", 1024 * 1024)
        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(invalid_file)
        assert 'Unsupported file extension.' in str(exc_info.value)

        large_file = MockFile("test.pdf", 11 * 1024 * 1024)
        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(large_file)
        assert "File too large" in str(exc_info.value)

        valid_file = MockFile("test.pdf", 1024 * 1024)
        assert validate_file_extension(valid_file) is None

    def test_phone_number_validation(self):
        """Test phone number validation"""
        # Valid numbers
        validate_phone_number("+1234567890")
        validate_phone_number("1234567890")
        
        # Invalid numbers
        with pytest.raises(ValidationError):
            validate_phone_number("123")  # Too short
        with pytest.raises(ValidationError):
            validate_phone_number("abcdefghij")  # Non-numeric