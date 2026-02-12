import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Folder, File

import json
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Folder, File # 모델 경로는 프로젝트에 맞게 수정하세요
from django.shortcuts import get_object_or_404
# 기존 import 유지 (ContentFile, JsonResponse 등)

# 1. 파일 내용 불러오기 (Read)
def get_file_content(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)
    try:
        # 파일 열기 (텍스트 모드)
        with file_obj.file.open('rb') as f:
            content = f.read().decode('utf-8') # 한글 깨짐 방지
        return JsonResponse({'status': 'success', 'filename': file_obj.name, 'content': content})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': '파일을 읽을 수 없습니다. 텍스트 파일이 아닌 것 같습니다.'})

# 2. 파일 내용 수정하기 (Update)
def update_file_content(request, file_id):
    if request.method == 'POST':
        try:
            file_obj = get_object_or_404(File, id=file_id)
            data = json.loads(request.body)
            new_content = data.get('content')
            
            # 기존 파일 삭제 후 새로 저장 (또는 덮어쓰기)
            # Django FileField는 기본적으로 덮어쓰지 않고 이름을 바꾸므로,
            # 명시적으로 내용을 교체하는 방식을 씁니다.
            
            # 1. 기존 파일 경로 가져오기
            file_name = file_obj.name 
            
            # 2. 파일 내용 덮어쓰기
            # 'w' 모드로 열어서 내용을 교체합니다.
            # 스토리지 설정에 따라 다르지만 로컬 파일시스템 기준입니다.
            with open(file_obj.file.path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # 3. 사이즈 업데이트
            file_obj.size = len(new_content.encode('utf-8'))
            file_obj.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'}, status=405)

def create_text_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            folder_id = data.get('folder_id')
            filename = data.get('filename')
            content = data.get('content')

            if not filename:
                return JsonResponse({'status': 'error', 'message': '파일 이름을 입력해주세요.'})

            # 확장자가 없으면 자동으로 .txt 붙이기
            if '.' not in filename:
                filename += '.txt'

            folder = None
            if folder_id:
                folder = Folder.objects.get(id=folder_id)

            # UTF-8로 인코딩하여 파일 생성
            file_content = ContentFile(content.encode('utf-8'))

            new_file = File(
                folder=folder,
                name=filename,
                size=file_content.size,
                # user=request.user # 사용자 필드가 있다면 주석 해제
            )

            # 실제 파일 저장
            new_file.file.save(filename, file_content)
            new_file.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

def root(request):
    folders = Folder.objects.filter(parent=None).order_by('name')
    files = File.objects.filter(folder=None).order_by('name')
    all_folders_root = Folder.objects.filter(parent=None).order_by('name')
    return render(request, 'core/explorer.html', {
        'folders': folders, 'files': files, 
        'all_folders_root': all_folders_root, 'current_folder': None, 'breadcrumbs': []
    })

def folder_view(request, folder_id):
    current_folder = get_object_or_404(Folder, id=folder_id)
    folders = current_folder.subfolders.all().order_by('name')
    files = current_folder.files.all().order_by('name')
    all_folders_root = Folder.objects.filter(parent=None).order_by('name')
    breadcrumbs = []
    p = current_folder.parent
    while p:
        breadcrumbs.insert(0, p)
        p = p.parent
    return render(request, 'core/explorer.html', {
        'folders': folders, 'files': files, 
        'all_folders_root': all_folders_root, 'current_folder': current_folder, 'breadcrumbs': breadcrumbs
    })

@require_POST
def move_item(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        target_id = data.get('target_id')
        target_folder = Folder.objects.filter(id=target_id).first() if target_id else None

        if item_type == 'folder':
            item = get_object_or_404(Folder, id=item_id)
            if target_folder:
                # 자기 자신 또는 하위 폴더로 이동 방지
                if target_folder.id == item.id:
                    return JsonResponse({'status': 'error', 'message': '자기 자신으로 이동할 수 없습니다.'})
                curr = target_folder
                while curr.parent:
                    if curr.parent.id == item.id:
                        return JsonResponse({'status': 'error', 'message': '하위 폴더로 이동할 수 없습니다.'})
                    curr = curr.parent
                if curr.id == item.id:
                    return JsonResponse({'status': 'error', 'message': '하위 폴더로 이동할 수 없습니다.'})
            item.parent = target_folder
        else:
            item = get_object_or_404(File, id=item_id)
            item.folder = target_folder
        
        item.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)
    return FileResponse(open(file_obj.file.path, 'rb'), as_attachment=True, filename=file_obj.name)

def create_folder(request, folder_id=None):
    if request.method == 'POST':
        name = request.POST.get('folder_name')
        if name:
            parent = get_object_or_404(Folder, id=folder_id) if folder_id else None
            Folder.objects.create(name=name, parent=parent)
    return redirect('folder', folder_id=folder_id) if folder_id else redirect('root')

def upload_file(request, folder_id):
    if request.method == 'POST':
        folder = get_object_or_404(Folder, id=folder_id)
        for f in request.FILES.getlist('files'):
            File.objects.create(file=f, folder=folder, name=f.name)
    return redirect('folder', folder_id=folder_id)

def delete_item(request, item_id):
    item_type = request.GET.get('type')
    redirect_to = 'root'
    if item_type == 'folder':
        item = get_object_or_404(Folder, id=item_id)
        if item.parent: redirect_to = item.parent.id
        item.delete()
    else:
        item = get_object_or_404(File, id=item_id)
        if item.folder: redirect_to = item.folder.id
        item.delete()
    return redirect('folder', folder_id=redirect_to) if isinstance(redirect_to, int) else redirect('root')

def logout_view(request):
    logout(request)
    return redirect('login')
