from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Folder, FileItem
import os

# ----------------------------------------------------------------
# 읽기 전용 권한 확인 함수
# ----------------------------------------------------------------
def check_readonly(user):
    # 1. 슈퍼유저(관리자)는 절대 읽기 전용 아님
    if user.is_superuser:
        return False
    # 2. 'ReadOnly'라는 그룹에 속해 있으면 읽기 전용
    return user.groups.filter(name='ReadOnly').exists()

# ----------------------------------------------------------------
# 1. 인증 관련 뷰
# ----------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('root')

    if request.method == 'POST':
        user_id = request.POST.get('username')
        user_pw = request.POST.get('password')
        user = authenticate(request, username=user_id, password=user_pw)
        
        if user is not None:
            login(request, user)
            return redirect('root')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ----------------------------------------------------------------
# 2. 메인 탐색기 (Root)
# ----------------------------------------------------------------
@login_required(login_url='login')
def root(request):
    # 읽기 전용 여부 확인
    is_readonly = check_readonly(request.user)
    
    root_folders = Folder.objects.filter(parent__isnull=True, owner=request.user).order_by('name')

    # POST 요청 (생성/업로드) - 읽기 전용이면 차단
    if request.method == 'POST':
        if is_readonly:
            messages.error(request, '읽기 전용 계정입니다.')
            return redirect('root')

        if 'new_folder' in request.POST:
            folder_name = request.POST.get('folder_name')
            if folder_name:
                Folder.objects.create(name=folder_name, parent=None, owner=request.user)
        
        if 'upload_file' in request.FILES:
            upload = request.FILES['upload_file']
            FileItem.objects.create(file=upload, parent=None, owner=request.user)
            return redirect('root')
        
        return redirect('root')

    folders = root_folders
    files = FileItem.objects.filter(parent__isnull=True, owner=request.user).order_by('-created_at')

    context = {
        'root_folders': root_folders,
        'current_folder': None,
        'folders': folders,
        'files': files,
        'path': [],
        'is_readonly': is_readonly,  # 템플릿으로 전달
    }
    return render(request, 'core/explorer.html', context)

# ----------------------------------------------------------------
# 3. 폴더 상세 보기
# ----------------------------------------------------------------
@login_required(login_url='login')
def folder_view(request, folder_id):
    is_readonly = check_readonly(request.user)
    
    current_folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    root_folders = Folder.objects.filter(parent__isnull=True, owner=request.user).order_by('name')

    if request.method == 'POST':
        if is_readonly:
            messages.error(request, '읽기 전용 계정입니다.')
            return redirect('folder', folder_id=folder_id)

        if 'new_folder' in request.POST:
            folder_name = request.POST.get('folder_name')
            if folder_name:
                Folder.objects.create(name=folder_name, parent=current_folder, owner=request.user)
        
        if 'upload_file' in request.FILES:
            upload = request.FILES['upload_file']
            FileItem.objects.create(file=upload, parent=current_folder, owner=request.user)
            return redirect('folder', folder_id=folder_id)
            
        return redirect('folder', folder_id=folder_id)

    subfolders = current_folder.subfolders.filter(owner=request.user).order_by('name')
    files = current_folder.files.filter(owner=request.user).order_by('-created_at')

    path = []
    temp = current_folder.parent
    while temp:
        path.insert(0, temp)
        temp = temp.parent

    context = {
        'root_folders': root_folders,
        'current_folder': current_folder,
        'folders': subfolders,
        'files': files,
        'path': path,
        'is_readonly': is_readonly, # 템플릿으로 전달
    }
    return render(request, 'core/explorer.html', context)

# ----------------------------------------------------------------
# 4. 삭제 기능
# ----------------------------------------------------------------
@login_required(login_url='login')
def delete_item(request, item_id):
    # 읽기 전용이면 삭제 불가
    if check_readonly(request.user):
        messages.error(request, '읽기 전용 계정은 삭제할 수 없습니다.')
        return redirect('root')

    item_type = request.GET.get('type')
    parent_id = None

    if item_type == 'folder':
        item = get_object_or_404(Folder, id=item_id, owner=request.user)
        if item.parent:
            parent_id = item.parent.id
        item.delete()
        
    elif item_type == 'file':
        item = get_object_or_404(FileItem, id=item_id, owner=request.user)
        if item.parent:
            parent_id = item.parent.id
        if item.file and os.path.isfile(item.file.path):
            try:
                os.remove(item.file.path)
            except OSError:
                pass
        item.delete()

    if parent_id:
        return redirect('folder', folder_id=parent_id)
    else:
        return redirect('root')