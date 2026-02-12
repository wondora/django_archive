import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Folder, File

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