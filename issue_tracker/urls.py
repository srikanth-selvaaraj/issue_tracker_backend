from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # auth urls
    path('api/login', UserLogin.as_view(), name='user_login'),
    path('api/register', UserRegister.as_view(), name='user_registration'),

    # jwt refresh token url
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # project crud
    path('api/projects', ProjectView.as_view(), name='project_list_create'),
    path('api/project/<int:pk>', ProjectDetailView().as_view(), name='project-update-delete'),    

    # issues crud
    path('api/issues', IssueView.as_view(), name="issue_list_create"),
]