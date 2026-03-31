from django.contrib import admin
from .models import AnalysisRecord


@admin.register(AnalysisRecord)
class AnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'analysis_type', 'user', 'status', 'created_at')
    list_filter = ('analysis_type', 'status')
    search_fields = ('original_filename', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
