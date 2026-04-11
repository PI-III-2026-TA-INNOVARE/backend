from rest_framework import serializers
from apps.resumes.models import Resume
from apps.educations.serializers import EducationSerializer
from apps.experiences.serializers import ExperienceSerializer
from apps.skills.serializers import SkillSerializer

class ResumeSerializer(serializers.ModelSerializer):
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    skill = SkillSerializer(many=True, read_only=True)

    class Meta:
        model  = Resume
        fields = ['id_resume', 'education', 'experience', 'skill']