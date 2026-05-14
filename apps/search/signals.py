from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.educations.models import Education
from apps.experiences.models import Experience
from apps.research.models import Research
from apps.researchers.models import Researcher
from apps.resumes.models import Resume
from apps.search.services import upsert_research_index, upsert_researcher_index


@receiver(post_save, sender=Researcher)
def researcher_saved(sender, instance, **kwargs):
    upsert_researcher_index(instance.id_researcher)


@receiver(post_delete, sender=Researcher)
def researcher_deleted(sender, instance, **kwargs):
    upsert_researcher_index(instance.id_researcher)


@receiver(post_save, sender=Research)
def research_saved(sender, instance, **kwargs):
    upsert_research_index(instance.id_research)


@receiver(post_delete, sender=Research)
def research_deleted(sender, instance, **kwargs):
    upsert_research_index(instance.id_research)


@receiver(post_save, sender=Education)
@receiver(post_delete, sender=Education)
def education_changed(sender, instance, **kwargs):
    researcher = Researcher.objects.filter(resume_id=instance.resume_id).first()
    if researcher:
        upsert_researcher_index(researcher.id_researcher)


@receiver(post_save, sender=Experience)
@receiver(post_delete, sender=Experience)
def experience_changed(sender, instance, **kwargs):
    researcher = Researcher.objects.filter(resume_id=instance.resume_id).first()
    if researcher:
        upsert_researcher_index(researcher.id_researcher)


@receiver(m2m_changed, sender=Resume.skill.through)
def resume_skills_changed(sender, instance, **kwargs):
    researcher = Researcher.objects.filter(resume_id=instance.id_resume).first()
    if researcher:
        upsert_researcher_index(researcher.id_researcher)


@receiver(m2m_changed, sender=Researcher.area.through)
def researcher_area_changed(sender, instance, **kwargs):
    upsert_researcher_index(instance.id_researcher)
