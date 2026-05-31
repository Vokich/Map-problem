from .forms import UserRegistrationForm
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem
from .forms import ProblemForm
import requests


def index(request):
  return render(request, 'index.html')

def map(request):
  problems = Problem.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
  problems_data = []

  for problem in problems:
    coords = {
      'lat': problem.latitude,
      'lng': problem.longitude,
      'title': problem.title,
      'description': problem.description[:100] + '...' if len(problem.description) > 100 else problem.description,
      'type': problem.get_problem_type_display(),
      'status': problem.get_status_display(),
      'url': problem.get_absolute_url()
    }
    problems_data.append(coords)

  return render(request, 'map.html', {'problems': problems_data, 'form': ProblemForm()})


def reg(request):
  if request.method == 'POST':
    form = UserRegistrationForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('index')
  else:
    form = UserRegistrationForm()

  return render(request, 'registration.html', {'form': form})

def login_form(request):
  if request.method == 'POST':
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(request, username=username, password=password)
      if user is not None:
        login(request, user)
        return redirect('index')
  else:
    form = LoginForm()

  return render(request, 'login.html', {'form': form})

def logout_form(request):
  logout(request)
  return redirect('/')


def problem_create(request):
  if request.method == 'POST':
    form = ProblemForm(request.POST, request.FILES)
    if form.is_valid():
      problem = form.save()
      problem.save()
      return redirect('problem_detail', pk=problem.pk)
  else:
    form = ProblemForm()
  return render(request, 'problem_form.html', {'form': form})


def problem_list_view(request):
  problems = Problem.objects.all()
  return render(request, 'problem_list.html', {'problems': problems})


def problem_detail_view(request, pk):
  problem = get_object_or_404(Problem, pk=pk)
  return render(request, 'problem_detail.html', {'problem': problem})
