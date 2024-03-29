
# Create your views here.

from rest_framework.response import Response
from django.shortcuts import render
from rest_framework import viewsets, views, permissions
from .models import User, Stock
from .serializers import UserSerializer, StockSerializer
from django.contrib import auth
from django.contrib.auth.hashers import make_password
from rest_framework.reverse import reverse
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .utils.monitor import start_engine, add_one_user, update_one_user, delete_one_user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        print(attrs)
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        # Add extra responses here
        data['username'] = self.user.username
        data['is_superuser'] = self.user.is_superuser
        data['user'] = reverse('user-detail', [self.user.id], request=self.context['request'])
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class IndexView(views.APIView):

    def get(self, request):
        # Redirect to a success page.
        return render(request, "index.html")


class LogoutView(views.APIView):

    def post(self, request):
        auth.logout(request)
        # Redirect to a success page.
        return Response({"code": 20000})


class UserView(views.APIView):
    """
    允许用户查看或编辑的API路径。
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (authentication.JWTAuthentication,)

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        confirmPassword = request.data.get('confirmPassword', '')
        dingding_token = request.data.get('dingding_token', '')
        polling_interval = request.data.get('polling_interval', 30)
        if password != confirmPassword:
            return Response({"code": 50008, "message": "两次输入密码不相同"})
        if User.objects.filter(username=username):
            return Response({"code": 50009, "message": "用户名已存在"})
        user = User.objects.create(
            username=username,
            password=make_password(password),
            dingding_token=dingding_token,
            polling_interval=polling_interval,
        )
        add_one_user(user.id)
        return Response({"code": 20000})


class UserPasswrodView(views.APIView):
    """
    允许用户查看或编辑的API路径。
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (authentication.JWTAuthentication,)

    def post(self, request):
        username = request.data.get('username', '')
        originPassword = request.data.get('originPassword', '')
        password = request.data.get('password', '')
        confirmPassword = request.data.get('confirmPassword', '')
        if password != confirmPassword:
            return Response({"code": 50008, "message": "两次输入密码不相同"})
        user = auth.authenticate(username=username, password=originPassword)
        if user is not None and user.is_active:
            # Correct password, and the user is marked "active"
            user.set_password(password)
            user.save()
            # Redirect to a success page.
            return Response({"code": 20000})
        return Response({"code": 50008, "message": "原密码不正确"})


class UserViewSet(viewsets.ModelViewSet):
    """
    允许用户查看或编辑的API路径。
    """
    # permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = (authentication.JWTAuthentication,)

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=self.request.user.id).order_by('-date_joined')

    def update(self, request, *args, **kwargs):
        res = super().update(request, *args, **kwargs)
        update_one_user(kwargs.get("pk"))
        return res

    def destroy(self, request, *args, **kwargs):
        res = super().destroy(request, *args, **kwargs)
        delete_one_user(kwargs.get("pk"))
        return res


class StockViewSet(viewsets.ModelViewSet):
    """
    允许用户查看或编辑的API路径。
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (authentication.JWTAuthentication,)

    queryset = Stock.objects.all().order_by('-id')
    serializer_class = StockSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Stock.objects.all().order_by('-id')
        return Stock.objects.filter(user=self.request.user).order_by('-id')


start_pool = False


class StartMonitorView(views.APIView):

    def get(self, request):
        global start_pool
        if not start_pool:
            start_engine()
            start_pool = True
        return Response({"code": 20000})
