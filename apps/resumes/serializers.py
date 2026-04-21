from rest_framework import serializers
from apps.resumes.models import Resume
from apps.educations.serializers import EducationSerializer
from apps.experiences.serializers import ExperienceSerializer
from apps.skills.serializers import SkillSerializer
from apps.skills.models import Skill

class ResumeSerializer(serializers.ModelSerializer):
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    skill = SkillSerializer(many=True, read_only=True)
    skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all(), source='skill', write_only=True, required=False)

    class Meta:
        model  = Resume
        fields = ['id_resume', 'education', 'experience', 'skill', 'skills']

    def create(self, validated_data):
        skills = validated_data.pop('skill', [])
        resume = Resume.objects.create(**validated_data)
        if skills:
            resume.skill.set(skills)
        return resume

    def update(self, instance, validated_data):
        skills = validated_data.pop('skill', None)
        instance = super().update(instance, validated_data)
        if skills is not None:
            instance.skill.set(skills)
        return instance
