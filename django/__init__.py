VERSION = (1, 8, 0, 'alpha', 0)


def get_version(*args, **kwargs):
    # Avoid circular import
    from django.utils.version import get_version
    return get_version(*args, **kwargs)


__version__ = get_version(VERSION)


def setup():
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    """
    from django.apps import apps
    from django.conf import settings
    from django.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    apps.populate(settings.INSTALLED_APPS)
