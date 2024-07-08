from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import CustomTokenObtainPairView, UserViewSet, OrganisationViewSet


router = SimpleRouter(trailing_slash=False)
router.register('api/organisations', OrganisationViewSet, basename='organisation')

urlpatterns = [
    path('auth/register', UserViewSet.as_view({'post': 'create'}, name='user-create')),
    path('auth/login', CustomTokenObtainPairView.as_view(), name='login'),
    path('api/users/<userId>', UserViewSet.as_view({'get': 'retrieve'}, name='user-retrieve')),
]

urlpatterns += router.urls
