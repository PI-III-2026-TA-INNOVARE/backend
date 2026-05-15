from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchingProfileViewSet, MatchViewSet, SmartSearchViewSet

router = DefaultRouter()
router.register(r'profiles', MatchingProfileViewSet, basename='matching-profile')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'search', SmartSearchViewSet, basename='smart-search')

urlpatterns = [
    path('', include(router.urls)),
]
