from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Comment, Problem


class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.ru'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Придумайте пароль'}),
    )
    password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите пароль'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {'username': 'Логин'}
        widgets = {'username': forms.TextInput(attrs={'placeholder': 'Введите логин'})}

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Пароли не совпадают.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Введите логин'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите пароль'}),
    )


class ProblemForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Problem
        fields = [
            'title', 'description', 'picture', 'problem_type',
            'address', 'latitude', 'longitude',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введите название проблемы'}),
            'description': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Опишите проблему подробнее'}
            ),
            'address': forms.TextInput(
                attrs={'placeholder': 'Адрес будет определен автоматически'}
            ),
        }

    def clean_latitude(self):
        lat = self.cleaned_data.get('latitude')
        if lat is not None and not (-90 <= lat <= 90):
            raise ValidationError('Некорректное значение широты.')
        return lat

    def clean_longitude(self):
        lng = self.cleaned_data.get('longitude')
        if lng is not None and not (-180 <= lng <= 180):
            raise ValidationError('Некорректное значение долготы.')
        return lng

    def clean_picture(self):
        uploaded = self.files.get('picture') if hasattr(self, 'files') else None
        if uploaded and uploaded.size > 5 * 1024 * 1024:
            raise ValidationError('Размер изображения не должен превышать 5 МБ.')
        return self.cleaned_data.get('picture')


class ProblemFilterForm(forms.Form):
    SORT_CHOICES = [
        ('-create_time', 'Сначала новые'),
        ('create_time', 'Сначала старые'),
        ('-votes', 'По голосам'),
    ]

    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + list(Problem.Status.choices),
        required=False,
        label='Статус',
    )
    problem_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + list(Problem.ProblemType.choices),
        required=False,
        label='Тип',
    )
    date_from = forms.DateField(
        required=False,
        label='Дата от',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label='Дата до',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Название или адрес'}),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        label='Сортировка',
    )


class StatusChangeForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['status']
        labels = {'status': 'Новый статус'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': ''}
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Напишите комментарий...',
                'class': 'comment-textarea',
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if len(text) < 3:
            raise ValidationError('Комментарий слишком короткий.')
        return text