from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "").strip()
        password = attrs.get("password")

        user = CustomUser.objects.filter(email__iexact=identifier).first()
        username = user.username if user else identifier
        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=username,
            password=password,
        )

        if not authenticated_user or not authenticated_user.is_active:
            raise serializers.ValidationError({"detail": "No active account found with the provided credentials."})

        refresh = self.get_token(authenticated_user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}