from django.db import models
from django.contrib.auth.models import User


class AnalysisRecord(models.Model):
    ANALYSIS_TYPE_CHOICES = [
        ('audio', '음성(회의) 분석'),
        ('video', '영상(CCTV) 분석'),
    ]
    STATUS_CHOICES = [
        ('pending', '대기 중'),
        ('processing', '처리 중'),
        ('done', '완료'),
        ('error', '오류'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=10, choices=ANALYSIS_TYPE_CHOICES)
    original_filename = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to='uploads/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 음성 분석 결과
    transcript = models.TextField(blank=True, null=True, verbose_name='STT 전문')
    summary_lines = models.JSONField(blank=True, null=True, verbose_name='핵심 요약 3줄')

    # 영상 분석 결과
    video_stats = models.JSONField(blank=True, null=True, verbose_name='경영 지표')
    safety_events = models.JSONField(blank=True, null=True, verbose_name='안전 경고 이벤트')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '분석 기록'
        verbose_name_plural = '분석 기록 목록'

    def __str__(self):
        return f"[{self.get_analysis_type_display()}] {self.original_filename} ({self.user.username})"
