from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.researchers.urls')),
    path('api/', include('apps.companies.urls')),
    path('api/', include('apps.educations.urls')),
    path('api/', include('apps.experiences.urls')),
    path('api/', include('apps.resumes.urls')),
    path('api/', include('apps.skills.urls')),
    path('api/', include('apps.universities.urls')),
    path('api/', include('apps.research.urls')),
    path('api/', include('apps.research_candidates.urls')),
    path('api/', include('apps.search.urls')),
    path('api/', include('apps.research_area.urls')),
    path('api/', include('apps.dashboard.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
