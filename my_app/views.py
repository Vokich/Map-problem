from datetime import timedelta

from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm, LoginForm, ProblemFilterForm, ProblemForm,
    StatusChangeForm, UserRegistrationForm,
)
from .models import Comment, Problem, ProblemVote, UserProfile, get_user_achievements


def index(request):
    stats = {
        'users': User.objects.count(),
        'problems': Problem.objects.count(),
        'completed': Problem.objects.filter(status=Problem.Status.COMPLETED).count(),
        'points': UserProfile.objects.aggregate(total=Count('id'))['total'] or 0,
    }
    total_points = 0
    for p in UserProfile.objects.all():
        total_points += p.points
    stats['points'] = total_points

    top_problems = (
        Problem.objects
        .annotate(votes_total=Count('votes'))
        .filter(votes_total__gt=0)
        .order_by('-votes_total')[:3]
    )

    return render(request, 'index.html', {'stats': stats, 'top_problems': top_problems})


def map(request):
    problems = (
        Problem.objects
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .annotate(votes_total=Count('votes'))
    )
    problems_data = []
    for p in problems:
        data = p.get_coordinates()
        if data:
            data['status_code'] = p.status
            data['votes'] = p.votes_total
            problems_data.append(data)

    return render(request, 'map.html', {'problems': problems_data, 'form': ProblemForm()})


def reg(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешна! Добро пожаловать.')
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
    return redirect('index')


@login_required
def problem_create(request):
    if request.method == 'POST':
        form = ProblemForm(request.POST, request.FILES)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.author = request.user
            problem.save()
            messages.success(request, 'Заявка успешно создана!')
            return redirect('problem_detail', pk=problem.pk)
    else:
        form = ProblemForm()
    return render(request, 'problem_form.html', {'form': form, 'is_edit': False})


@login_required
def problem_edit(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    if problem.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете редактировать эту заявку.')
        return redirect('problem_detail', pk=pk)

    if request.method == 'POST':
        form = ProblemForm(request.POST, request.FILES, instance=problem)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка обновлена.')
            return redirect('problem_detail', pk=pk)
    else:
        form = ProblemForm(instance=problem)
    return render(request, 'problem_form.html', {
        'form': form, 'is_edit': True, 'problem': problem,
    })


@login_required
def problem_delete(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    if problem.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете удалить эту заявку.')
        return redirect('problem_detail', pk=pk)

    if request.method == 'POST':
        problem.delete()
        messages.success(request, 'Заявка удалена.')
        return redirect('problem_list')
    return render(request, 'problem_confirm_delete.html', {'problem': problem})


@login_required
def problem_change_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Только модераторы могут менять статус.')
        return redirect('problem_detail', pk=pk)

    problem = get_object_or_404(Problem, pk=pk)
    if request.method == 'POST':
        old_status = problem.status
        form = StatusChangeForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Статус изменён на «{problem.get_status_display()}».'
            )

            if (
                old_status != problem.status
                and problem.author
                and problem.author.email
            ):
                send_mail(
                    subject=f'Статус вашей заявки «{problem.title}» изменён',
                    message=(
                        f'Здравствуйте, {problem.author.username}!\n\n'
                        f'Статус вашей заявки «{problem.title}» изменён.\n'
                        f'Новый статус: {problem.get_status_display()}.\n\n'
                        f'Подробности: '
                        f'{request.build_absolute_uri(problem.get_absolute_url())}\n\n'
                        f'— Сайт «Проблемы городов»'
                    ),
                    from_email=None,
                    recipient_list=[problem.author.email],
                    fail_silently=True,
                )
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def problem_vote(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    vote, created = ProblemVote.objects.get_or_create(
        problem=problem, user=request.user
    )
    if created:
        messages.success(request, 'Голос учтён! Спасибо, что поддерживаете.')
    else:
        vote.delete()
        messages.info(request, 'Голос отозван.')
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def comment_add(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.problem = problem
        comment.author = request.user
        comment.save()

        if problem.author and problem.author.email and problem.author != request.user:
            send_mail(
                subject=f'Новый комментарий к заявке «{problem.title}»',
                message=(
                    f'Здравствуйте, {problem.author.username}!\n\n'
                    f'{request.user.username} оставил комментарий:\n'
                    f'«{comment.text}»\n\n'
                    f'Подробности: '
                    f'{request.build_absolute_uri(problem.get_absolute_url())}\n\n'
                    f'— Сайт «Проблемы городов»'
                ),
                from_email=None,
                recipient_list=[problem.author.email],
                fail_silently=True,
            )

        messages.success(request, 'Комментарий добавлен.')
    else:
        messages.error(request, 'Не удалось добавить комментарий.')
    return redirect('problem_detail', pk=pk)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    problem_pk = comment.problem_id
    if comment.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете удалить этот комментарий.')
        return redirect('problem_detail', pk=problem_pk)

    comment.delete()
    messages.success(request, 'Комментарий удалён.')
    return redirect('problem_detail', pk=problem_pk)


def _paginate_query_string(request):
    q = request.GET.copy()
    q.pop('page', None)
    return q.urlencode()


def problem_list_view(request):
    problems = Problem.objects.annotate(votes_total=Count('votes'))
    filter_form = ProblemFilterForm(request.GET or None)

    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        if cd.get('status'):
            problems = problems.filter(status=cd['status'])
        if cd.get('problem_type'):
            problems = problems.filter(problem_type=cd['problem_type'])
        if cd.get('date_from'):
            problems = problems.filter(create_time__date__gte=cd['date_from'])
        if cd.get('date_to'):
            problems = problems.filter(create_time__date__lte=cd['date_to'])
        if cd.get('search'):
            s = cd['search']
            problems = problems.filter(Q(title__icontains=s) | Q(address__icontains=s))
        if cd.get('sort'):
            problems = problems.order_by(cd['sort'])

    paginator = Paginator(problems, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'problem_list.html', {
        'problems': page_obj,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'query_string': _paginate_query_string(request),
        'is_my_problems': False,
    })


@login_required
def my_problems_view(request):
    problems = (
        Problem.objects
        .filter(author=request.user)
        .annotate(votes_total=Count('votes'))
    )
    paginator = Paginator(problems, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'problem_list.html', {
        'problems': page_obj,
        'page_obj': page_obj,
        'filter_form': ProblemFilterForm(),
        'query_string': _paginate_query_string(request),
        'is_my_problems': True,
    })


def problem_detail_view(request, pk):
    problem = get_object_or_404(Problem, pk=pk)

    can_edit = (
        request.user.is_authenticated
        and (request.user == problem.author or request.user.is_staff)
    )
    status_form = None
    if request.user.is_authenticated and request.user.is_staff:
        status_form = StatusChangeForm(instance=problem)

    user_voted = False
    if request.user.is_authenticated:
        user_voted = ProblemVote.objects.filter(
            problem=problem, user=request.user
        ).exists()

    comments = problem.comments.select_related('author').all()
    comment_form = CommentForm()

    return render(request, 'problem_detail.html', {
        'problem': problem,
        'can_edit': can_edit,
        'status_form': status_form,
        'user_voted': user_voted,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Доступ только для администраторов.')
        return redirect('index')

    problems = Problem.objects.all()
    total = problems.count()

    stats = {
        'total': total,
        'new': problems.filter(status=Problem.Status.NEW).count(),
        'in_progress': problems.filter(status=Problem.Status.IN_PROGRESS).count(),
        'completed': problems.filter(status=Problem.Status.COMPLETED).count(),
        'rejected': problems.filter(status=Problem.Status.REJECTED).count(),
    }

    types_data = [
        (label, problems.filter(problem_type=code).count())
        for code, label in Problem.ProblemType.choices
    ]

    six_months_ago = timezone.now() - timedelta(days=180)
    months_qs = (
        problems
        .filter(create_time__gte=six_months_ago)
        .annotate(month=TruncMonth('create_time'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months_labels = []
    months_values = []
    for row in months_qs:
        months_labels.append(row['month'].strftime('%m.%Y'))
        months_values.append(row['count'])

    statuses_chart = [
        {'label': 'Новые', 'value': stats['new'], 'color': '#2365a5'},
        {'label': 'В процессе', 'value': stats['in_progress'], 'color': '#d49a2d'},
        {'label': 'Решены', 'value': stats['completed'], 'color': '#187647'},
        {'label': 'Отклонены', 'value': stats['rejected'], 'color': '#a53d3d'},
    ]

    week_ago = timezone.now() - timedelta(days=7)
    week_count = problems.filter(create_time__gte=week_ago).count()

    return render(request, 'admin_dashboard.html', {
        'stats': stats,
        'types_data': types_data,
        'recent': problems.order_by('-create_time')[:8],
        'week_count': week_count,
        'months_labels': months_labels,
        'months_values': months_values,
        'statuses_chart': statuses_chart,
    })


def leaderboard_view(request):
    for user in User.objects.filter(profile__isnull=True):
        UserProfile.objects.create(user=user)

    profiles = (
        UserProfile.objects
        .select_related('user')
        .order_by('-points')[:20]
    )

    my_achievements = None
    my_profile = None
    my_rank = None
    if request.user.is_authenticated:
        my_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        my_achievements = get_user_achievements(request.user)
        my_rank = (
            UserProfile.objects.filter(points__gt=my_profile.points).count() + 1
        )

    return render(request, 'leaderboard.html', {
        'profiles': profiles,
        'my_profile': my_profile,
        'my_achievements': my_achievements,
        'my_rank': my_rank,
    })


def qr_code_view(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    url = request.build_absolute_uri(reverse('problem_detail', args=[pk]))

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#5143d0', back_color='white')

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')