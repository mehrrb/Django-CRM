from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

def preprocessing_filter_spec(endpoints):
    """Filter API endpoints for documentation"""
    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        # Only include API endpoints
        if path.startswith("/api/"):
            filtered.append((path, path_regex, method, callback))
    return filtered

class CustomAutoSchema(AutoSchema):
    """Custom schema for API documentation"""
    
    def get_operation_id(self):
        """Generate readable operation IDs"""
        model = self.view.__class__.__name__.replace('ViewSet', '')
        action = self.method_mapping[self.method.lower()]
        return f"{model}_{action}"

    def get_tags(self):
        """Group endpoints by model name"""
        model = self.view.__class__.__name__.replace('ViewSet', '')
        return [model]

common_parameters = [
    OpenApiParameter(
        name='org',
        type=str,
        location=OpenApiParameter.HEADER,
        description='Organization ID',
        required=True
    ),
    OpenApiParameter(
        name='Authorization',
        type=str,
        location=OpenApiParameter.HEADER,
        description='Bearer {token}',
        required=True
    )
]
