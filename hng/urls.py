from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    # path('api/users/<userId>',),
    # path('api/organisations',),
    # path('api/organisations/<orgId>',),
    # path('api/organisations/<orgId>/users',),
]
