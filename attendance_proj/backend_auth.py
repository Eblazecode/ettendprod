from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging


logger = logging.getLogger(__name__)

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, admin_password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(admin_email=username)
            if user.check_password(admin_password):
                user.backend = 'attendance_proj.backend_auth.EmailBackend'
                return user
            else:
                logger.warning(f"Password mismatch for user {username}")
        except UserModel.DoesNotExist:
            logger.warning(f"User with email {username} does not exist")
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None