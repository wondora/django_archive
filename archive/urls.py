from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'), # core.views.logout_view 호출
    
    path('', views.root, name='root'),
    path('folder/<int:folder_id>/', views.folder_view, name='folder'),
    path('folder/create/', views.create_folder, name='create_root_folder'),
    path('folder/<int:folder_id>/create/', views.create_folder, name='create_folder'),
    path('folder/<int:folder_id>/upload/', views.upload_file, name='upload_file'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    
    # 다운로드 경로 추가
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('move/', views.move_item, name='move_item'),
    path('move/', views.move_item, name='move_item'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)