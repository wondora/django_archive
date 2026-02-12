import os  # 👈 name 설정을 위해 반드시 필요합니다.
from django.db import models

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class File(models.Model):
    file = models.FileField(upload_to='uploads/')
    folder = models.ForeignKey(Folder, null=True, blank=True, related_name='files', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField(default=0, editable=False)  # 파일 크기 자동 저장
    created_at = models.DateTimeField(auto_now_add=True)

    # ▼ 관리자 페이지에서 'File items' 대신 'Files'로 보이게 설정
    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"

    def save(self, *args, **kwargs):
        # 파일 저장 시 이름과 크기 자동 설정
        if self.file:
            if not self.name:
                # 업로드된 파일의 순수 이름을 추출하여 저장
                self.name = os.path.basename(self.file.name)
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "Untitled File"