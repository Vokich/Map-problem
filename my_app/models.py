from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Problem(models.Model):
    class ProblemType(models.TextChoices):
        INFRASTRUCTURE = 'infrastructure', 'Инфраструктура'
        SAFETY = 'safety', 'Безопасность'
        BEAUTIFICATION = 'beautification', 'Благоустройство'
        SOCIAL = 'social', 'Социальное'
        OTHER = 'other', 'Другое'

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Решена'
        REJECTED = 'rejected', 'Отклонена'

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='problems',
        verbose_name='Автор',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    picture = models.ImageField(
        upload_to='problems/%Y/%m/%d/',
        verbose_name='Фото',
        null=True,
        blank=True,
    )
    problem_type = models.CharField(
        max_length=50,
        choices=ProblemType.choices,
        default=ProblemType.OTHER,
        verbose_name='Тип проблемы',
    )
    address = models.CharField(max_length=300, verbose_name='Адрес объекта')
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
    )
    latitude = models.FloatField(verbose_name='Широта', null=True, blank=True)
    longitude = models.FloatField(verbose_name='Долгота', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    completion_rewarded = models.BooleanField(
        default=False,
        verbose_name='Баллы за решение начислены',
    )

    class Meta:
        verbose_name = 'Проблема'
        verbose_name_plural = 'Проблемы'
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def get_absolute_url(self):
        return reverse('problem_detail', kwargs={'pk': self.pk})

    @property
    def votes_count(self):
        return self.votes.count()

    def get_coordinates(self):
        if self.latitude is not None and self.longitude is not None:
            short_desc = (
                f'{self.description[:100]}...'
                if len(self.description) > 100
                else self.description
            )
            return {
                'lat': self.latitude,
                'lng': self.longitude,
                'title': self.title,
                'description': short_desc,
                'type': self.get_problem_type_display(),
                'status': self.get_status_display(),
                'url': self.get_absolute_url(),
            }
        return None


class ProblemVote(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name='Заявка',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата голоса')

    class Meta:
        unique_together = ('problem', 'user')
        verbose_name = 'Голос'
        verbose_name_plural = 'Голоса'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.problem.title}'


class Comment(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Заявка',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(max_length=1000, verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author.username}: {self.text[:50]}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    points = models.IntegerField(default=0, verbose_name='Баллы')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        ordering = ['-points']

    LEVELS = [0, 50, 150, 300, 600, 1000]

    @property
    def level(self):
        current = 1
        for i, threshold in enumerate(self.LEVELS, start=1):
            if self.points >= threshold:
                current = i
        return current

    @property
    def next_level_points(self):
        for threshold in self.LEVELS:
            if self.points < threshold:
                return threshold
        return None

    @property
    def progress_percent(self):
        if self.level >= len(self.LEVELS):
            return 100
        prev = self.LEVELS[self.level - 1]
        nxt = self.LEVELS[self.level]
        span = nxt - prev
        if span <= 0:
            return 100
        return int((self.points - prev) / span * 100)

    def add_points(self, amount):
        self.points += amount
        self.save(update_fields=['points'])

    def __str__(self):
        return f'{self.user.username} ({self.points} баллов)'


ACHIEVEMENTS = [
    {'code': 'first_problem', 'name': 'Первая заявка', 'desc': 'Создайте первую заявку', 'icon': '🎯', 'goal': 1},
    {'code': 'five_problems', 'name': 'Активист', 'desc': 'Создайте 5 заявок', 'icon': '🏃', 'goal': 5},
    {'code': 'ten_problems', 'name': 'Борец за справедливость', 'desc': 'Создайте 10 заявок', 'icon': '⚔️', 'goal': 10},
    {'code': 'first_completed', 'name': 'Первый успех', 'desc': 'Первая решённая заявка', 'icon': '✅', 'goal': 1},
    {'code': 'five_completed', 'name': 'Герой города', 'desc': '5 решённых заявок', 'icon': '🏆', 'goal': 5},
    {'code': 'level_3', 'name': 'Опытный', 'desc': 'Достигните 3 уровня', 'icon': '⭐', 'goal': 3},
]


def get_user_achievements(user):
    problems = Problem.objects.filter(author=user)
    total = problems.count()
    completed = problems.filter(status=Problem.Status.COMPLETED).count()
    profile = getattr(user, 'profile', None)
    level = profile.level if profile else 1

    progress_map = {
        'first_problem': (min(total, 1), 1, total >= 1),
        'five_problems': (min(total, 5), 5, total >= 5),
        'ten_problems': (min(total, 10), 10, total >= 10),
        'first_completed': (min(completed, 1), 1, completed >= 1),
        'five_completed': (min(completed, 5), 5, completed >= 5),
        'level_3': (min(level, 3), 3, level >= 3),
    }

    result = []
    for ach in ACHIEVEMENTS:
        cur, goal, unlocked = progress_map[ach['code']]
        result.append({**ach, 'current': cur, 'goal': goal, 'unlocked': unlocked})
    return result