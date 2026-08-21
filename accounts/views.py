from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response({'detail': 'Invalid email or password.'}, status=401)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({'access': access_token})
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,
        )
        return response


# BUG WE HIT (and fixed): just re-stringifying a token object with str(refresh)
# does NOT create a new token — it's the same token, same signature, every time.
# Real rotation requires: blacklist the old one, then mutate its identity
# (set_jti/set_exp/set_iat) BEFORE converting it to a string. Verified this by
# comparing token strings across two /refresh/ calls in curl — they must differ.
class RefreshView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        raw_refresh = request.COOKIES.get('refresh_token')

        if raw_refresh is None:
            return Response({'detail': 'No refresh token found.'}, status=401)

        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return Response({'detail': 'Invalid or expired refresh token.'}, status=401)

        access_token = str(refresh.access_token)
        response = Response({'access': access_token})

        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
            if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION'):
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60,
            )

        return response

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        raw_refresh = request.COOKIES.get('refresh_token')

        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except TokenError:
                pass

        response = Response({'detail': 'Logged out successfully.'})
        response.delete_cookie('refresh_token')
        return response