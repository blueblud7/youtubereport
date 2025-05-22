from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Channel, Report
from youtube_service import YouTubeService
from flask_migrate import Migrate
import os
from datetime import datetime
from gpt_service import GPTService
import re
import markdown

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
    
    channel = Channel(name=name, channel_id=channel_id, channel_type=type)
    db.session.add(channel)
    db.session.commit()
    
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
    videos = youtube_service.get_videos(channel.name, is_keyword=(channel.channel_type == 'keyword'))
    
    if not videos:
        flash('비디오를 찾을 수 없습니다.')
        return redirect(url_for('index'))
    
    # 각 비디오의 자막 가져오기 및 분석
    analyses = []
    analyzed_videos = []  # 실제로 분석된 비디오들의 정보 저장
    
    for video in videos[:5]:  # 최근 5개 비디오만 분석
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=3000) 