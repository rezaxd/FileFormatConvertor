from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

app_name = "convertor"
urlpatterns = [
    path('', views.step1, name='step1'),
    path('convert/', views.step2, name='step2'),
    path('convert-list/', views.step3, name='step3'),
    path('delete/<str:task_id>/', views.delete, name='delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
