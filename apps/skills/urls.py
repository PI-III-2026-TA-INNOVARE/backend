from django.urls import path
from .views import SkillCreateListView, SkillRetrieveUpdateDestroy

urlpatterns = [
    path('skills/', SkillCreateListView.as_view(), name='skill-create-list'),
    path('skills/<int:pk>', SkillRetrieveUpdateDestroy.as_view(), name='skill-detail-view'),
]