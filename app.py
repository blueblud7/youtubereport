from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from models import db, Channel, Report
from youtube_service import YouTubeService
from scheduler_service import SchedulerService
from flask_migrate import Migrate
import os
from datetime import datetime
from gpt_service import GPTService
import re
import markdown
from translations import get_text, get_all_texts

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youtube_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'  # 실제 운영 환경에서는 안전한 키로 변경해야 합니다

db.init_app(app)
migrate = Migrate(app, db)

# 서비스 인스턴스 생성
youtube_service = YouTubeService()

def get_gpt_service():
    return GPTService()

# 언어 설정 함수
def get_current_language():
    """현재 언어 설정을 반환합니다."""
    return session.get('language', 'ko')

@app.context_processor
def inject_language():
    """모든 템플릿에 언어 관련 변수를 주입합니다."""
    current_lang = get_current_language()
    return {
        'current_lang': current_lang,
        'texts': get_all_texts(current_lang),
        '_': lambda key: get_text(key, current_lang)
    }

@app.route('/set_language/<language>')
def set_language(language):
    """언어를 설정합니다."""
    if language in ['ko', 'en']:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

# nl2br 필터 추가
@app.template_filter('nl2br')
def nl2br(text):
    """줄바꿈을 <br> 태그로 변환"""
    return text.replace('\n', '<br>') if text else ''

# 마크다운 필터 추가
@app.template_filter('markdown')
def markdown_filter(text):
    """마크다운을 HTML로 변환"""
    if not text:
        return ''
    
    # 마크다운을 HTML로 변환
    md = markdown.Markdown(extensions=['nl2br', 'fenced_code'])
    html_content = md.convert(text)
    
    # URL을 클릭 가능한 링크로 변환 (새 창에서 열기)
    import re
    url_pattern = r'(https?://[^\s<>"]+)'
    html_content = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', html_content)
    
    return html_content

@app.route('/')
def index():
    channels = Channel.query.all()
    return render_template('index.html', channels=channels)

@app.route('/reports')
def all_reports():
    channels = Channel.query.all()
    return render_template('all_reports.html', channels=channels)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    name = request.form.get('name')
    type = request.form.get('type')
    video_count = int(request.form.get('video_count', 5))
    target_channel = request.form.get('target_channel', '')
    
    # 자동 리포트 설정
    auto_report_enabled = request.form.get('auto_report_enabled') == 'on'
    schedule_time = request.form.get('schedule_time', '09:00')
    schedule_days = request.form.get('schedule_days', 'daily')
    auto_prompt_type = request.form.get('auto_prompt_type', 'simple')
    
    if not name or not type:
        flash('채널 이름과 타입을 모두 입력해주세요.')
        return redirect(url_for('index'))
    
    # 채널 ID 설정
    channel_id = None
    if type == 'channel':
        channel_id = youtube_service._extract_channel_id(name)
        if not channel_id:
            flash('유효하지 않은 채널입니다.')
            return redirect(url_for('index'))
    
    # 키워드의 경우 target_channel_id 설정
    target_channel_id = None
    if type == 'keyword' and target_channel:
        target_channel_id = target_channel
    
    channel = Channel(
        name=name, 
        channel_id=channel_id, 
        channel_type=type,
        video_count=video_count,
        target_channel_id=target_channel_id,
        auto_report_enabled=auto_report_enabled,
        schedule_time=schedule_time,
        schedule_days=schedule_days,
        auto_prompt_type=auto_prompt_type
    )
    db.session.add(channel)
    db.session.commit()
    
    auto_status = "자동 리포트 활성화" if auto_report_enabled else "수동 리포트만"
    flash(f'"{name}"이(가) 성공적으로 추가되었습니다! (분석 비디오 수: {video_count}개, {auto_status})')
    return redirect(url_for('index'))

@app.route('/generate_report/<int:channel_id>')
def generate_report(channel_id):
    """프롬프트 선택 페이지로 리다이렉트"""
    return redirect(url_for('prompt_selection', channel_id=channel_id))

@app.route('/prompt_selection/<int:channel_id>')
def prompt_selection(channel_id):
    """프롬프트 선택 페이지"""
    channel = Channel.query.get_or_404(channel_id)
    return render_template('prompt_selection.html', channel=channel)

@app.route('/generate_report_with_prompt/<int:channel_id>', methods=['POST'])
def generate_report_with_prompt(channel_id):
    """선택된 프롬프트로 리포트 생성"""
    import json
    
    channel = Channel.query.get_or_404(channel_id)
    youtube_service = YouTubeService()
    
    # 폼 데이터 가져오기
    prompt_type = request.form.get('prompt_type', 'simple')
    
    if prompt_type == 'custom':
        word_count = int(request.form.get('word_count', 500))
        language = request.form.get('language', 'ko')
        custom_prompt = request.form.get('custom_prompt', '')
    else:
        word_count = int(request.form.get('basic_word_count', 500))
        language = request.form.get('basic_language', 'ko')
        custom_prompt = None
    
    # 비디오 가져오기
    videos = youtube_service.get_videos(
        channel.name, 
        is_keyword=(channel.channel_type == 'keyword'),
        target_channel_id=channel.target_channel_id
    )
    
    if not videos:
        flash('비디오를 찾을 수 없습니다.')
        return redirect(url_for('index'))
    
    # 각 비디오의 자막 가져오기 및 분석
    analyses = []
    analyzed_videos = []  # 실제로 분석된 비디오들의 정보 저장
    
    for video in videos[:channel.video_count]:  # 설정된 개수만큼 분석
        captions = youtube_service.get_video_captions(video['video_id'])
        if captions:
            analysis = get_gpt_service().analyze_content(
                captions, 
                prompt_type=prompt_type, 
                language=language, 
                word_count=word_count, 
                custom_prompt=custom_prompt
            )
            if analysis:
                analyses.append(analysis)
                analyzed_videos.append(video)  # 분석된 비디오 정보 저장
    
    if not analyses:
        flash('분석할 수 있는 자막이 없습니다.')
        return redirect(url_for('index'))
    
    # 리포트 생성 (참고문헌 포함)
    report_content = get_gpt_service().generate_daily_report(
        analyses, 
        prompt_type=prompt_type, 
        language=language, 
        word_count=word_count, 
        custom_prompt=custom_prompt,
        references=analyzed_videos
    )
    
    # 참고문헌 정보를 JSON으로 저장
    references_json = json.dumps(analyzed_videos, ensure_ascii=False)
    
    # 리포트 저장
    report = Report(
        channel_id=channel.id, 
        content=report_content, 
        report_type='daily',
        prompt_type=prompt_type,
        custom_prompt=custom_prompt,
        word_count=word_count,
        language=language,
        references=references_json
    )
    db.session.add(report)
    db.session.commit()
    
    flash(f'"{channel.name}"의 리포트가 성공적으로 생성되었습니다!')
    return redirect(url_for('all_reports'))

@app.route('/view_report/<int:report_id>')
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template('report.html', report=report)

@app.route('/delete_channel/<int:channel_id>', methods=['POST'])
def delete_channel(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    
    # 연관된 리포트들도 함께 삭제
    Report.query.filter_by(channel_id=channel_id).delete()
    
    # 채널 삭제
    db.session.delete(channel)
    db.session.commit()
    
    flash(f'"{channel.name}" 이(가) 성공적으로 삭제되었습니다.')
    return redirect(url_for('index'))

@app.route('/update_schedule/<int:channel_id>', methods=['POST'])
def update_schedule(channel_id):
    """채널의 자동 리포트 스케줄을 업데이트합니다."""
    channel = Channel.query.get_or_404(channel_id)
    
    # 폼 데이터 가져오기
    auto_report_enabled = request.form.get('auto_report_enabled') == 'on'
    schedule_time = request.form.get('schedule_time', '09:00')
    schedule_days = request.form.get('schedule_days', 'daily')
    auto_prompt_type = request.form.get('auto_prompt_type', 'simple')
    
    # 데이터베이스 업데이트
    channel.auto_report_enabled = auto_report_enabled
    channel.schedule_time = schedule_time
    channel.schedule_days = schedule_days
    channel.auto_prompt_type = auto_prompt_type
    
    db.session.commit()
    
    status = "활성화" if auto_report_enabled else "비활성화"
    flash(f'"{channel.name}"의 자동 리포트 스케줄이 {status}되었습니다!')
    return redirect(url_for('index'))

@app.route('/schedule_status')
def schedule_status():
    """현재 스케줄 상태를 JSON으로 반환합니다."""
    scheduler_service = SchedulerService(app)
    
    try:
        next_runs = scheduler_service.get_next_scheduled_runs()
        enabled_channels = Channel.query.filter_by(auto_report_enabled=True).all()
        
        return jsonify({
            'enabled_channels': len(enabled_channels),
            'next_runs': next_runs,
            'scheduler_running': scheduler_service.running
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_auto_report/<int:channel_id>')
def test_auto_report(channel_id):
    """특정 채널의 자동 리포트를 즉시 테스트 실행합니다."""
    scheduler_service = SchedulerService(app)
    
    channel = Channel.query.get_or_404(channel_id)
    
    if not channel.auto_report_enabled:
        flash(f'"{channel.name}"의 자동 리포트가 비활성화되어 있습니다.')
        return redirect(url_for('index'))
    
    try:
        # 백그라운드에서 리포트 생성 실행
        import threading
        thread = threading.Thread(
            target=scheduler_service._generate_auto_report, 
            args=(channel_id,), 
            daemon=True
        )
        thread.start()
        
        flash(f'"{channel.name}"의 자동 리포트 테스트가 시작되었습니다. 잠시 후 리포트를 확인해주세요.')
    except Exception as e:
        flash(f'자동 리포트 테스트 중 오류가 발생했습니다: {e}')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 스케줄러 서비스 초기화 및 시작
        scheduler_service = SchedulerService(app)
        scheduler_service.start_scheduler()
        
        print("🚀 YouTube 리포트 시스템이 시작되었습니다!")
        print("📅 자동 리포트 스케줄러가 활성화되었습니다!")
        
    try:
        app.run(debug=True, port=3000)
    finally:
        # 애플리케이션 종료 시 스케줄러 정리
        if scheduler_service:
            scheduler_service.stop_scheduler() 