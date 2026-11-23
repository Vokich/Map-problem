from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('map/', views.map, name='map'),

    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_form, name='logout'),

    path('problems/', views.problem_list_view, name='problem_list'),
    path('problems/my/', views.my_problems_view, name='my_problems'),
    path('problems/create/', views.problem_create, name='problem_create'),
    path('problems/<int:pk>/', views.problem_detail_view, name='problem_detail'),
    path('problems/<int:pk>/edit/', views.problem_edit, name='problem_edit'),
    path('problems/<int:pk>/delete/', views.problem_delete, name='problem_delete'),
    path('problems/<int:pk>/change-status/', views.problem_change_status, name='problem_change_status'),
    path('problems/<int:pk>/vote/', views.problem_vote, name='problem_vote'),
    path('problems/<int:pk>/comment/', views.comment_add, name='comment_add'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('problems/<int:pk>/qr/', views.qr_code_view, name='problem_qr'),

    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.txt',
        subject_template_name='password_reset_subject.txt',
        success_url=reverse_lazy('auth'),
    ), name='password_reset'),

    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        success_url=reverse_lazy('auth'),
    ), name='password_reset_confirm'),
]