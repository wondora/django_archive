from django.db import models
from django.contrib.auth.models import User
import os

class Folder(models.Model):
    name = models.CharField(max_length=255)
    # 상위 폴더 (재귀적 관계: 폴더 안에 폴더)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    # 작성자 (로그인 기능 연동)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FileItem(models.Model):
    # 실제 파일 업로드 경로
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)  # 파일 크기 저장
    
    # 어떤 폴더에 속해 있는지
    parent = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    # 작성자
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 파일 저장 시 이름과 크기를 자동으로 채움
        if self.file:
            if not self.name:
                self.name = os.path.basename(self.file.name)
            if not self.size:
                self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    @property
    def is_folder(self):
        return False
        
    # 템플릿에서 폴더와 파일을 구분하기 위해 Folder 모델에도 속성 추가
    Folder.add_to_class('is_folder', True)