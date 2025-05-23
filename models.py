from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    channel_id = db.Column(db.String(100), nullable=True)
    channel_type = db.Column(db.String(20), nullable=False)  # 'channel' or 'keyword'
    video_count = db.Column(db.Integer, nullable=False, default=5)  # 분석할 비디오 개수
    target_channel_id = db.Column(db.String(100), nullable=True)  # 키워드 검색 제한할 채널 ID
    
    # 자동 리포트 생성 스케줄링 필드들
    auto_report_enabled = db.Column(db.Boolean, nullable=False, default=False)  # 자동 리포트 활성화 여부
    schedule_time = db.Column(db.String(5), nullable=True, default="09:00")  # 실행 시간 (HH:MM 형식)
    schedule_days = db.Column(db.String(20), nullable=False, default="daily")  # 실행 주기 (daily, weekdays, weekend)
    auto_prompt_type = db.Column(db.String(20), nullable=False, default='simple')  # 자동 리포트용 프롬프트 타입
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reports = db.relationship('Report', backref='channel', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Channel {self.name}>'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    report_type = db.Column(db.String(20), nullable=False, default='daily')  # 'daily', 'weekly', etc.
    prompt_type = db.Column(db.String(20), nullable=False, default='simple')  # 'simple', 'professional', 'bullet', 'custom'
    custom_prompt = db.Column(db.Text, nullable=True)  # 커스텀 프롬프트
    word_count = db.Column(db.Integer, nullable=True, default=500)  # 글자수
    language = db.Column(db.String(10), nullable=False, default='ko')  # 언어
    references = db.Column(db.Text, nullable=True)  # 참고문헌 (JSON 형식)

    def __repr__(self):
        return f'<Report {self.id} for Channel {self.channel_id}>' 