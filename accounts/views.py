from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailOrUsernameTokenObtainPairSerializer


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
	serializer_class = EmailOrUsernameTokenObtainPairSerializer
from django.shortcuts import render

# Create your views here.
