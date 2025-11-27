from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView

from authentication.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

from .models import User

try:
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )
    BLACKLIST_ENABLED = True
except ImportError:
    BLACKLIST_ENABLED = False


def is_token_blacklisted(token_string):
    """Check if a refresh token is blacklisted."""
    if not BLACKLIST_ENABLED:
        return False

    try:
        token = RefreshToken(token_string)
        jti = token.get('jti')

        # Check if the token exists in outstanding tokens and is blacklisted
        outstanding_token = OutstandingToken.objects.filter(jti=jti).first()
        if not outstanding_token:
            return False

        return BlacklistedToken.objects.filter(token=outstanding_token).exists()
    except Exception:
        return False


def set_jwt_cookies(response, access_token=None, refresh_token=None):
    secure_cookie = getattr(settings, "SESSION_COOKIE_SECURE", False)
    access_max_age = 86400
    refresh_max_age = 604800
    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure_cookie,
            max_age=access_max_age,
            path="/"
        )
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            max_age=refresh_max_age,
            path="/"
        )

class LoginViewSet(viewsets.ModelViewSet):
    serializer_class = CustomTokenObtainPairSerializer
    queryset = None

    def create(self, request, *args, **kwargs):
        serializer= self.get_serializer(data=request.data)
        if serializer.is_valid():
            access = serializer.validated_data.get('access')
            refresh= serializer.validated_data.get('refresh')
            response = Response(serializer.validated_data, status=HTTP_200_OK)
            set_jwt_cookies(response, access, refresh)
            return response
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterSerializer
    queryset = None

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)
            refresh_str = str(refresh)

            response = Response({
                "message": "User created successfully",
                "user": UserSerializer(user).data,
                "access_token": access,
                "refresh_token" : refresh_str
            }, status=HTTP_201_CREATED)

            set_jwt_cookies(response, access, refresh_str)
            return response
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class LogoutView(TokenBlacklistView):
    def post(self, request):
        response = super().post(request)

        if response.status_code == HTTP_200_OK:
            resp = Response({
                "message": "User logged out successfully"
            }, status=HTTP_200_OK)
            resp.delete_cookie("access_token", path='/')
            resp.delete_cookie("refresh_token", path='/')
            return resp
        return response

class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        serializer = self.get_serializer(request.user)
        return Response({
            "message" : "User fetched successfully",
            "user" : serializer.data
        }, status=HTTP_200_OK)

class RefreshViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TokenRefreshSerializer
    queryset = User.objects.none()

    def post(self, request):
        refresh_token = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=HTTP_400_BAD_REQUEST)

        try:
            serializer = self.get_serializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)

            access_token = serializer.validated_data["access"]
            new_refresh_token = serializer.validated_data.get("refresh", refresh_token)

            response = Response(
                {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                },
                status=HTTP_200_OK,
            )
            set_jwt_cookies(response, access_token, new_refresh_token)
            return response
        except TokenError as e:
            error_message = str(e)
            if "blacklisted" in error_message.lower():
                return Response(
                    {"detail": "Token is blacklisted. Please login again."},
                    status=HTTP_400_BAD_REQUEST
                )
            return Response(
                {"detail": f"Invalid or expired token: {error_message}"},
                status=HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"], url_path="check", permission_classes=[AllowAny])
    def check(self, request):
        """Check if a refresh token is blacklisted."""
        refresh_token = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=HTTP_400_BAD_REQUEST)

        is_blacklisted = is_token_blacklisted(refresh_token)

        return Response({
            "is_blacklisted": is_blacklisted,
            "message": "Token is blacklisted" if is_blacklisted else "Token is valid"
        }, status=HTTP_200_OK)
