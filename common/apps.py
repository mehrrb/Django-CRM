from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    name = "common"
    verbose_name = _("Common")

    def ready(self):
        """
        Import signal handlers when the app is ready
        This ensures all models are loaded before connecting signals
        """
        try:
            import common.signals
            import common.receivers
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error importing signals: {str(e)}")
