from rest_framework.routers import DefaultRouter
from .views import PropostaViewSet

router = DefaultRouter()
router.register(r'propostas', PropostaViewSet, basename='proposta')

urlpatterns = router.urls
