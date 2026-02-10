from django.contrib import admin
from django.urls import path
from core import views  # core 앱의 views 전체를 가져옴
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. 로그인 / 로그아웃
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 2. 메인 페이지 (루트) -> views.root 사용
    path('', views.root, name='root'),

    # 3. 폴더 상세 페이지 -> views.folder_view 사용
    path('folder/<int:folder_id>/', views.folder_view, name='folder'),

    # 4. 삭제 기능
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
]

# 개발 모드일 때 미디어 파일 서빙 설정 (필수)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)