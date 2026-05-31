from django.contrib import admin
from my_app import views
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('map/', views.map, name='map'),
    path('reg', views.reg, name='registration'),
    path('login', views.login_form, name='login'),
    path('logout/', views.logout_form, name="logout"),
    path('problem/create/', views.problem_create, name='problem_create'),
    path('list_of_problems', views.problem_list_view, name='problem_list'),
    path('problem/<int:pk>/', views.problem_detail_view, name='problem_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
