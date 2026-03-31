import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import AnalysisRecord
from . import services


ALLOWED_AUDIO_EXT = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'}
ALLOWED_VIDEO_EXT = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
MAX_FILE_MB = 200


def home(request):
    """공개 랜딩 페이지. 로그인 불필요."""
    return render(request, 'analysis/home.html')


def register(request):
    """회원가입 뷰. 이미 로그인 상태면 대시보드로."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"환영합니다, {user.username}님! 계정이 생성되었습니다.")
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'analysis/register.html', {'form': form})


# ──────────────────────────────────────────────
# 대시보드 (로그인 필수)
# ──────────────────────────────────────────────

@login_required
def dashboard(request):
    """메인 업로드 대시보드."""
    recent_records = AnalysisRecord.objects.filter(user=request.user)[:10]
    return render(request, 'analysis/dashboard.html', {
        'recent_records': recent_records,
    })


# ──────────────────────────────────────────────
# 업로드 처리
# ──────────────────────────────────────────────

def _validate_file(uploaded_file, allowed_exts: set, label: str):
    """파일 확장자·크기 검증. 문제 시 ValueError 발생."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in allowed_exts:
        raise ValueError(f"지원하지 않는 {label} 형식입니다. 허용: {', '.join(sorted(allowed_exts))}")
    if uploaded_file.size > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"파일 크기는 {MAX_FILE_MB}MB 이하만 허용됩니다.")


@login_required
@require_http_methods(["POST"])
def upload_audio(request):
    """음성 파일 업로드 → Whisper STT → TF-IDF 요약."""
    uploaded = request.FILES.get('audio_file')
    if not uploaded:
        messages.error(request, "파일을 선택해 주세요.")
        return redirect('dashboard')

    try:
        _validate_file(uploaded, ALLOWED_AUDIO_EXT, "오디오")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('dashboard')

    # DB 레코드 생성 (pending)
    record = AnalysisRecord.objects.create(
        user=request.user,
        analysis_type='audio',
        original_filename=uploaded.name,
        uploaded_file=uploaded,
        status='processing',
    )

    try:
        result = services.analyze_audio(record.uploaded_file.path)
        record.transcript = result['transcript']
        record.summary_lines = result['summary_lines']
        record.status = 'done'
    except Exception as exc:
        record.status = 'error'
        record.transcript = f"분석 중 오류 발생: {exc}"
        record.summary_lines = []
    finally:
        record.save()

    return redirect('report', record_id=record.id)


@login_required
@require_http_methods(["POST"])
def upload_video(request):
    """영상 파일 업로드 → OpenCV 메타 + Mock 경영/안전 분석."""
    uploaded = request.FILES.get('video_file')
    if not uploaded:
        messages.error(request, "파일을 선택해 주세요.")
        return redirect('dashboard')

    try:
        _validate_file(uploaded, ALLOWED_VIDEO_EXT, "영상")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('dashboard')

    record = AnalysisRecord.objects.create(
        user=request.user,
        analysis_type='video',
        original_filename=uploaded.name,
        uploaded_file=uploaded,
        status='processing',
    )

    try:
        result = services.analyze_video(record.uploaded_file.path)
        record.video_stats = result['video_stats']
        record.safety_events = result['safety_events']
        record.status = 'done'
    except Exception as exc:
        record.status = 'error'
        record.video_stats = {}
        record.safety_events = [{"message": f"분석 중 오류 발생: {exc}", "level": "danger", "timestamp": "00:00:00"}]
    finally:
        record.save()

    return redirect('report', record_id=record.id)


# ──────────────────────────────────────────────
# 리포트
# ──────────────────────────────────────────────

@login_required
def report(request, record_id: int):
    """분석 결과 리포트 페이지."""
    record = get_object_or_404(AnalysisRecord, id=record_id, user=request.user)

    # ECharts용 데이터 직렬화
    chart_data = None
    if record.analysis_type == 'video' and record.video_stats:
        stats = record.video_stats
        hourly = stats.get('hourly_distribution', [])
        chart_data = {
            'hours': [h['hour'] for h in hourly],
            'counts': [h['count'] for h in hourly],
            'total_visitors': stats.get('total_visitors', 0),
            'avg_stay': stats.get('avg_stay_minutes', 0),
            'peak_hour': stats.get('peak_hour', 'N/A'),
        }

    return render(request, 'analysis/report.html', {
        'record': record,
        'chart_data': chart_data,
    })
