from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Comment, Problem, ProblemVote, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(pre_save, sender=Problem)
def remember_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Problem.objects.get(pk=instance.pk).status
        except Problem.DoesNotExist:
            pass


@receiver(post_save, sender=Problem)
def award_problem_points(sender, instance, created, **kwargs):
    if not instance.author:
        return

    if created:
        profile, _ = UserProfile.objects.get_or_create(user=instance.author)
        profile.add_points(10)
        return

    old_status = getattr(instance, '_old_status', None)
    if (
        old_status != instance.status
        and instance.status == Problem.Status.COMPLETED
        and not instance.completion_rewarded
    ):
        profile, _ = UserProfile.objects.get_or_create(user=instance.author)
        profile.add_points(50)
        Problem.objects.filter(pk=instance.pk).update(completion_rewarded=True)


@receiver(post_save, sender=ProblemVote)
def award_vote_points(sender, instance, created, **kwargs):
    if created and instance.problem.author:
        profile, _ = UserProfile.objects.get_or_create(user=instance.problem.author)
        profile.add_points(1)


@receiver(post_save, sender=Comment)
def award_comment_points(sender, instance, created, **kwargs):
    if created:
        profile, _ = UserProfile.objects.get_or_create(user=instance.author)
        profile.add_points(2)