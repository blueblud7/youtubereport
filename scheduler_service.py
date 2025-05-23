import schedule
import threading
import time
from datetime import datetime, timedelta
from models import Channel, Report, db
from youtube_service import YouTubeService
from gpt_service import GPTService
import logging

class SchedulerService:
    def __init__(self, app):
        self.app = app
        self.youtube_service = YouTubeService()
        self.gpt_service = GPTService()
        self.running = False
        self.scheduler_thread = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_scheduler(self):
        """스케줄러를 백그라운드에서 시작합니다."""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("📅 자동 리포트 스케줄러가 시작되었습니다.")
    
    def stop_scheduler(self):
        """스케줄러를 중지합니다."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("⏹️ 자동 리포트 스케줄러가 중지되었습니다.")
    
    def _run_scheduler(self):
        """스케줄러 메인 루프"""
        with self.app.app_context():
            # 기존 스케줄 초기화
            schedule.clear()
            
            # 활성화된 채널들의 스케줄 설정
            self._setup_schedules()
            
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # 1분마다 체크
                    
                    # 5분마다 스케줄 재설정 (DB 변경사항 반영)
                    if datetime.now().minute % 5 == 0:
                        self._setup_schedules()
                        
                except Exception as e:
                    self.logger.error(f"스케줄러 실행 중 오류: {e}")
                    time.sleep(60)
    
    def _setup_schedules(self):
        """데이터베이스에서 활성화된 채널들의 스케줄을 설정합니다."""
        try:
            enabled_channels = Channel.query.filter_by(auto_report_enabled=True).all()
            
            # 기존 스케줄 초기화
            schedule.clear()
            
            for channel in enabled_channels:
                self._create_schedule_for_channel(channel)
                
            self.logger.info(f"📋 {len(enabled_channels)}개 채널의 자동 리포트 스케줄이 설정되었습니다.")
            
        except Exception as e:
            self.logger.error(f"스케줄 설정 중 오류: {e}")
    
    def _create_schedule_for_channel(self, channel):
        """개별 채널에 대한 스케줄을 생성합니다."""
        try:
            schedule_time = channel.schedule_time or "09:00"
            schedule_days = channel.schedule_days or "daily"
            
            # 스케줄 생성 함수
            def job():
                self._generate_auto_report(channel.id)
            
            # 실행 주기에 따른 스케줄 설정
            if schedule_days == "daily":
                schedule.every().day.at(schedule_time).do(job)
            elif schedule_days == "weekdays":
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                    getattr(schedule.every(), day).at(schedule_time).do(job)
            elif schedule_days == "weekend":
                schedule.every().saturday.at(schedule_time).do(job)
                schedule.every().sunday.at(schedule_time).do(job)
            
            self.logger.info(f"⏰ '{channel.name}' 채널 스케줄 설정: {schedule_days} {schedule_time}")
            
        except Exception as e:
            self.logger.error(f"채널 '{channel.name}' 스케줄 설정 오류: {e}")
    
    def _generate_auto_report(self, channel_id):
        """자동 리포트를 생성합니다."""
        try:
            with self.app.app_context():
                channel = Channel.query.get(channel_id)
                if not channel or not channel.auto_report_enabled:
                    return
                
                self.logger.info(f"🤖 '{channel.name}' 채널 자동 리포트 생성 시작...")
                
                # 비디오 분석
                videos = self.youtube_service.get_videos(
                    channel.name, 
                    is_keyword=(channel.channel_type == 'keyword'),
                    video_count=channel.video_count,
                    target_channel_id=channel.target_channel_id
                )
                
                if not videos:
                    self.logger.warning(f"'{channel.name}' 채널에서 비디오를 찾을 수 없습니다.")
                    return
                
                analyses = []
                for video in videos:
                    try:
                        captions = self.youtube_service.get_video_captions(video['video_id'])
                        if captions:
                            analyses.append({
                                'title': video['title'],
                                'url': video['url'],
                                'captions': captions,
                                'published_at': video.get('published_at', ''),
                                'view_count': video.get('view_count', 0)
                            })
                    except Exception as e:
                        self.logger.warning(f"비디오 '{video['title']}' 분석 중 오류: {e}")
                        continue
                
                if not analyses:
                    self.logger.warning(f"'{channel.name}' 채널에서 분석 가능한 비디오가 없습니다.")
                    return
                
                # 리포트 생성
                report_content = self.gpt_service.generate_daily_report(
                    analyses,
                    prompt_type=channel.auto_prompt_type,
                    language='ko',
                    word_count=500
                )
                
                # 참고문헌 생성
                references = [{'title': analysis['title'], 'url': analysis['url']} for analysis in analyses]
                
                # 데이터베이스에 저장
                new_report = Report(
                    channel_id=channel.id,
                    content=report_content,
                    report_type='auto',
                    prompt_type=channel.auto_prompt_type,
                    word_count=500,
                    language='ko',
                    references=str(references)
                )
                
                db.session.add(new_report)
                db.session.commit()
                
                self.logger.info(f"✅ '{channel.name}' 채널 자동 리포트 생성 완료! (Report ID: {new_report.id})")
                
        except Exception as e:
            self.logger.error(f"자동 리포트 생성 중 오류 (Channel ID: {channel_id}): {e}")
    
    def get_next_scheduled_runs(self):
        """다음 예정된 실행 시간들을 반환합니다."""
        try:
            next_runs = []
            for job in schedule.jobs:
                next_runs.append({
                    'job': str(job),
                    'next_run': job.next_run
                })
            return next_runs
        except Exception as e:
            self.logger.error(f"스케줄 조회 오류: {e}")
            return [] 