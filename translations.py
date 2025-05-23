# 다국어 지원을 위한 번역 사전
TRANSLATIONS = {
    'ko': {
        # 기본 시스템
        'youtube_report_system': 'YouTube 리포트 시스템',
        'channel_management': '채널/키워드',
        'all_reports': '리포트',
        
        # 메인 페이지
        'add_new_channel': '새 채널/키워드 추가',
        'channel_name_or_keyword': '채널 이름 또는 키워드',
        'channel_name_placeholder': '예: 체슬리TV',
        'keyword_placeholder': '예: 인공지능',
        'type': '타입 선택',
        'channel': '유튜브 채널',
        'keyword': '키워드 검색',
        'advanced_options': '고급 옵션',
        'video_count': '분석할 비디오 개수',
        'limit_to_specific_channel': '검색 범위 제한 (선택사항)',
        'channel_id_placeholder': '채널 ID (선택사항)',
        'auto_report_settings': '자동 리포트 설정',
        'enable_auto_report': '자동 리포트 생성',
        'schedule_time': '실행 시간',
        'schedule_frequency': '실행 주기',
        'daily': '매일',
        'weekdays': '평일만 (월~금)',
        'weekend': '주말만 (토~일)',
        'auto_prompt_type': '리포트 스타일',
        'simple': '간단한 요약',
        'detailed': '상세한 분석',
        'trend': '트렌드 분석',
        'add_channel': '채널 추가',
        'registered_channels': '등록된 채널/키워드',
        'no_channels': '등록된 채널이 없습니다',
        'generate_report': '리포트 생성',
        'delete': '삭제',
        'edit': '수정',
        'test': '테스트',
        'view_report': '리포트 보기',
        'created_at': '생성일',
        'auto_report': '자동 리포트',
        'enabled': '활성화',
        'disabled': '비활성화',
    },
    'en': {
        # 기본 시스템
        'youtube_report_system': 'YouTube Report System',
        'channel_management': 'Channels/Keywords',
        'all_reports': 'Reports',
        
        # 메인 페이지
        'add_new_channel': 'Add New Channel/Keyword',
        'channel_name_or_keyword': 'Channel Name or Keyword',
        'channel_name_placeholder': 'e.g., Chesley TV',
        'keyword_placeholder': 'e.g., artificial intelligence',
        'type': 'Type Selection',
        'channel': 'YouTube Channel',
        'keyword': 'Keyword Search',
        'advanced_options': 'Advanced Options',
        'video_count': 'Number of Videos to Analyze',
        'limit_to_specific_channel': 'Limit Search Scope (Optional)',
        'channel_id_placeholder': 'Channel ID (Optional)',
        'auto_report_settings': 'Auto Report Settings',
        'enable_auto_report': 'Enable Auto Report',
        'schedule_time': 'Schedule Time',
        'schedule_frequency': 'Schedule Frequency',
        'daily': 'Daily',
        'weekdays': 'Weekdays Only (Mon-Fri)',
        'weekend': 'Weekends Only (Sat-Sun)',
        'auto_prompt_type': 'Report Style',
        'simple': 'Simple Summary',
        'detailed': 'Detailed Analysis',
        'trend': 'Trend Analysis',
        'add_channel': 'Add Channel',
        'registered_channels': 'Registered Channels/Keywords',
        'no_channels': 'No registered channels',
        'generate_report': 'Generate Report',
        'delete': 'Delete',
        'edit': 'Edit',
        'test': 'Test',
        'view_report': 'View Report',
        'created_at': 'Created',
        'auto_report': 'Auto Report',
        'enabled': 'Enabled',
        'disabled': 'Disabled',
    }
}

def get_text(key, language='ko'):
    """특정 키에 대한 번역 텍스트를 반환합니다."""
    return TRANSLATIONS.get(language, {}).get(key, key)

def get_all_texts(language='ko'):
    """해당 언어의 모든 번역 텍스트를 반환합니다."""
    return TRANSLATIONS.get(language, {}) 