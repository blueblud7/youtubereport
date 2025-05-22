import os
from datetime import datetime
from youtube_service import YouTubeService
from gpt_service import GPTService
from config import REPORT_DIR
import json

class YouTubeReportGenerator:
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.gpt_service = GPTService()

    def process_channel(self, channel_input: str) -> list:
        """채널의 비디오들을 처리합니다."""
        print(f"Processing channel: {channel_input}")
        videos = self.youtube_service.get_channel_videos(channel_input)
        analyses = []

        for video in videos:
            print(f"Processing video: {video['title']}")
            captions = self.youtube_service.get_video_captions(video['video_id'])
            
            if captions:
                analysis = self.gpt_service.analyze_video_content(video, captions)
                if analysis:
                    analyses.append(analysis)

        return analyses

    def process_keyword(self, keyword: str) -> list:
        """키워드로 검색된 비디오들을 처리합니다."""
        print(f"Processing keyword: {keyword}")
        videos = self.youtube_service.search_videos(keyword)
        analyses = []

        for video in videos:
            print(f"Processing video: {video['title']}")
            captions = self.youtube_service.get_video_captions(video['video_id'])
            
            if captions:
                analysis = self.gpt_service.analyze_video_content(video, captions)
                if analysis:
                    analyses.append(analysis)

        return analyses

    def generate_report(self, analyses: list, report_type: str) -> str:
        """일일 리포트를 생성합니다."""
        report = self.gpt_service.generate_daily_report(analyses)
        
        if report:
            # 리포트 저장
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"{report_type}_{today}.txt"
            filepath = os.path.join(REPORT_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            return filepath
        return None

def main():
    generator = YouTubeReportGenerator()
    
    # 예시 채널 (다양한 형식 지원)
    channels = [
        "@손경제",  # 핸들 형식
        "https://www.youtube.com/@sonkyungjae",  # URL 형식
        "https://www.youtube.com/channel/UCQfwfsi5VrQ8yKZ-VWJJs7w",  # 채널 ID URL 형식
        "UCQfwfsi5VrQ8yKZ-VWJJs7w",  # 채널 ID 형식
    ]
    
    keywords = [
        "인공지능",
        "머신러닝",
    ]
    
    # 채널 분석
    for channel in channels:
        analyses = generator.process_channel(channel)
        if analyses:
            report_path = generator.generate_report(analyses, f"channel_{channel.replace('@', '').replace('https://www.youtube.com/', '')}")
            if report_path:
                print(f"Channel report generated: {report_path}")
    
    # 키워드 분석
    for keyword in keywords:
        analyses = generator.process_keyword(keyword)
        if analyses:
            report_path = generator.generate_report(analyses, f"keyword_{keyword}")
            if report_path:
                print(f"Keyword report generated: {report_path}")

if __name__ == "__main__":
    main() 