from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Problem(models.Model):
    objects = None
    PROBLEM_TYPES = (
      ('infrastructure', 'Инфраструктура'),
      ('safety', 'Безопасность'),
      ('beautification', 'Благоустройство'),
      ('social', 'Социальное'),
      ('other', 'Другое'),
    )

    STATUS_CHOICES = (
      ('new', 'Новая'),
      ('in_progress', 'В процессе'),
      ('completed', 'Решена'),
      ('rejected', 'Отклонена'),
    )

    title = models.CharField(max_length=100, verbose_name="Название", null=False, blank=False)
    description = models.TextField(max_length=1000, verbose_name="Описание", null=False, blank=False)
    picture = models.ImageField(upload_to='images', verbose_name="Фото", null=True, blank=True)
    problem_type = models.CharField(max_length=50, choices=PROBLEM_TYPES)
    address = models.CharField(max_length=300, verbose_name="Адрес обьекта", null=False, blank=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    latitude = models.FloatField(verbose_name="Широта", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Долгота", null=True, blank=True)
    create_time = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
      return reverse('problem_detail', kwargs={'pk': self.pk})


    def get_coordinates(self):
      if self.latitude and self.longitude:
        return {
          'lat': self.latitude,
          'lng': self.longitude,
          'title': self.title,
          'description': self.description[:100] + '...' if len(self.description) > 100 else self.description,
          'type': self.get_problem_type_display(),
          'status': self.get_status_display(),
          'url': self.get_absolute_url()
        }
      return None



