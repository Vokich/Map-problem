from django import forms
from django.contrib.auth.models import User
from .models import Problem
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
import os
from django.conf import settings


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            file_path = os.path.join(settings.BASE_DIR, "users.txt")
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"Username: {self.cleaned_data['username']}\n")
                f.write(f"Email: {self.cleaned_data['email']}\n")
                f.write(f"Password: {self.cleaned_data['password']}\n\n")

        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class ProblemForm(forms.ModelForm):
  latitude = forms.FloatField(
    widget=forms.HiddenInput(),
    required=False
  )
  longitude = forms.FloatField(
    widget=forms.HiddenInput(),
    required=False
  )

  class Meta:
    model = Problem
    fields = ['title', 'description', 'picture', 'problem_type', 'address', 'latitude', 'longitude']
    widgets = {
      'description': forms.Textarea(attrs={'rows': 4}),
      'title': forms.TextInput(attrs={'placeholder': 'Введите название проблемы'}),
      'address': forms.TextInput(attrs={'placeholder': 'Адрес будет определен автоматически'}),
    }
