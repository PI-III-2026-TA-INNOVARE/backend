from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.educations.models import Education
from apps.experiences.models import Experience
from apps.research.models import Research
from apps.research_candidates.services import run_match_for_research, run_match_for_researcher
from apps.researchers.models import Researcher
from apps.resumes.models import Resume


def _trigger_researcher_match_by_resume_id(resume_id):
    researcher = Researcher.objects.filter(resume_id=resume_id).first()
    if researcher:
        run_match_for_researcher(researcher.id_researcher)


@receiver(post_save, sender=Research)
def research_saved(sender, instance, **kwargs):
    run_match_for_research(instance.id_research)


@receiver(post_delete, sender=Research)
def research_deleted(sender, instance, **kwargs):
    # Delecao em cascata remove candidatos associados automaticamente.
    return


@receiver(post_save, sender=Researcher)
def researcher_saved(sender, instance, **kwargs):
    run_match_for_researcher(instance.id_researcher)


@receiver(post_delete, sender=Researcher)
def researcher_deleted(sender, instance, **kwargs):
    # Delecao em cascata remove candidatos associados automaticamente.
    return


@receiver(post_save, sender=Education)
@receiver(post_delete, sender=Education)
def education_changed(sender, instance, **kwargs):
    _trigger_researcher_match_by_resume_id(instance.resume_id)


@receiver(post_save, sender=Experience)
@receiver(post_delete, sender=Experience)
def experience_changed(sender, instance, **kwargs):
    _trigger_researcher_match_by_resume_id(instance.resume_id)


@receiver(m2m_changed, sender=Resume.skill.through)
def resume_skill_changed(sender, instance, action, **kwargs):
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return
    _trigger_researcher_match_by_resume_id(instance.id_resume)


@receiver(m2m_changed, sender=Researcher.area.through)
def researcher_area_changed(sender, instance, action, **kwargs):
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return
    run_match_for_researcher(instance.id_researcher)
