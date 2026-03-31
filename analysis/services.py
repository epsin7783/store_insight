"""
services.py — 로컬 AI 처리 모듈

- analyze_audio : Whisper STT + TF-IDF 추출 요약
- analyze_video : OpenCV 메타 읽기 + Mock 경영/안전 지표 생성
"""

import os
import random
import math
import numpy as np


# ──────────────────────────────────────────────
# 1. 음성 분석 (Whisper STT + TF-IDF 추출 요약)
# ──────────────────────────────────────────────

def _load_whisper():
    """Whisper 모델을 지연 로드 (앱 시작 시 불필요한 메모리 점유 방지)."""
    import whisper
    return whisper.load_model("base")


def _extractive_summary(text: str, top_n: int = 3) -> list[str]:
    """
    TF-IDF 기반 추출 요약.
    문장을 벡터화 → 각 문장의 TF-IDF 점수 합 → 상위 top_n 문장 반환.
    """
    import re
    from sklearn.feature_extraction.text import TfidfVectorizer

    # 문장 분리 (마침표·줄바꿈·느낌표·물음표 기준)
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if len(s.strip()) > 10]

    if not sentences:
        return [text[:200]] if text else ["요약할 내용이 없습니다."]

    if len(sentences) <= top_n:
        return sentences

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        # 문장별 TF-IDF 점수 합산 → 중요도 지표
        scores = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
        top_indices = scores.argsort()[::-1][:top_n]
        # 원문 순서 유지
        top_indices_sorted = sorted(top_indices)
        return [sentences[i] for i in top_indices_sorted]
    except Exception:
        return sentences[:top_n]


def analyze_audio(file_path: str) -> dict:
    """
    오디오 파일을 Whisper로 STT 변환 후 TF-IDF 추출 요약.

    Returns:
        {
            "transcript": str,          # 전체 텍스트
            "summary_lines": list[str]  # 핵심 문장 3줄
        }
    """
    model = _load_whisper()
    result = model.transcribe(file_path, language="ko")
    transcript = result.get("text", "").strip()

    summary_lines = _extractive_summary(transcript, top_n=3)

    return {
        "transcript": transcript,
        "summary_lines": summary_lines,
    }


# ──────────────────────────────────────────────
# 2. 영상 분석 (OpenCV 메타 + Mock 경영/안전 지표)
# ──────────────────────────────────────────────

def _generate_mock_visitors(duration_sec: float) -> dict:
    """영상 길이(초)에 비례한 가상 경영 지표 생성."""
    # 1분당 약 8~15명 방문 가정
    minutes = duration_sec / 60
    visitors = int(minutes * random.uniform(8, 15))
    avg_stay_min = round(random.uniform(3.5, 12.0), 1)

    # 시간대별 방문객 분포 (bar chart용)
    hours = max(1, math.ceil(duration_sec / 3600))
    hourly = []
    for h in range(hours):
        hourly.append({
            "hour": f"{10 + h:02d}:00",
            "count": random.randint(max(1, visitors // (hours * 2)), visitors // hours + 1),
        })

    return {
        "total_visitors": visitors,
        "avg_stay_minutes": avg_stay_min,
        "peak_hour": hourly[0]["hour"] if hourly else "N/A",
        "hourly_distribution": hourly,
    }


def _generate_mock_safety_events(duration_sec: float) -> list[dict]:
    """영상 길이에 비례한 가상 안전 경고 이벤트 타임라인 생성."""
    event_templates = [
        {"type": "crowd",   "level": "warning", "message": "군집 밀집 경고 (밀도 임계값 초과)"},
        {"type": "fall",    "level": "danger",  "message": "쓰러짐 의심 객체 탐지"},
        {"type": "loiter",  "level": "info",    "message": "장시간 배회 객체 감지"},
        {"type": "intrude", "level": "danger",  "message": "비업무 구역 침입 감지"},
        {"type": "fire",    "level": "danger",  "message": "연기/불꽃 패턴 감지 (확인 필요)"},
        {"type": "crowd",   "level": "info",    "message": "계산대 앞 혼잡 감지"},
    ]

    # 영상 1분당 0~1개 이벤트 생성 (최소 1개, 최대 8개)
    minutes = max(1, duration_sec / 60)
    n_events = min(8, max(1, int(minutes * random.uniform(0.3, 0.8))))

    events = []
    used_times = set()
    for _ in range(n_events):
        # 중복 없는 타임스탬프
        for attempt in range(20):
            t_sec = random.randint(10, int(duration_sec) - 5)
            if t_sec not in used_times:
                used_times.add(t_sec)
                break
        else:
            continue

        hh = 10 + t_sec // 3600
        mm = (t_sec % 3600) // 60
        ss = t_sec % 60
        template = random.choice(event_templates)
        events.append({
            "timestamp": f"{hh:02d}:{mm:02d}:{ss:02d}",
            "timestamp_sec": t_sec,
            "type": template["type"],
            "level": template["level"],
            "message": template["message"],
        })

    # 시간순 정렬
    events.sort(key=lambda e: e["timestamp_sec"])
    return events


def analyze_video(file_path: str) -> dict:
    """
    OpenCV로 영상 메타(프레임 수, 길이)를 읽은 뒤
    Mock 경영 지표 + 안전 이벤트를 반환.

    Returns:
        {
            "duration_sec": float,
            "total_frames": int,
            "fps": float,
            "video_stats": dict,    # 경영 지표
            "safety_events": list   # 안전 경고 타임라인
        }
    """
    import cv2

    cap = cv2.VideoCapture(file_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # FPS가 0이면 25로 fallback
    if fps <= 0:
        fps = 25.0

    duration_sec = total_frames / fps if total_frames > 0 else 60.0

    video_stats = _generate_mock_visitors(duration_sec)
    safety_events = _generate_mock_safety_events(duration_sec)

    return {
        "duration_sec": round(duration_sec, 2),
        "total_frames": total_frames,
        "fps": round(fps, 2),
        "video_stats": video_stats,
        "safety_events": safety_events,
    }
