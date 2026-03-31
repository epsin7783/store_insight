from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 공개 홈 (랜딩 페이지)
    path('', views.home, name='home'),

    # 인증
    path('login/', auth_views.LoginView.as_view(template_name='analysis/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # 핵심 기능 (로그인 필수)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/audio/', views.upload_audio, name='upload_audio'),
    path('upload/video/', views.upload_video, name='upload_video'),
    path('report/<int:record_id>/', views.report, name='report'),
]
