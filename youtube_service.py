from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from typing import List, Dict, Optional
import json
from config import YOUTUBE_API_KEYS, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION
import time
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

class YouTubeService:
    def __init__(self):
        self.api_keys = YOUTUBE_API_KEYS
        self.current_key_index = 0
        self.youtube = self._build_youtube_client()

    def _build_youtube_client(self):
        """YouTube API 클라이언트를 생성합니다."""
        return build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=self.api_keys[self.current_key_index]
        )

    def _switch_api_key(self):
        """API 키 할당량이 소진되면 다음 키로 전환합니다."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.youtube = self._build_youtube_client()

    def _extract_channel_id(self, channel_input: str) -> Optional[str]:
        """다양한 형식의 채널 입력에서 채널 ID를 추출합니다."""
        try:
            # URL 형식 처리
            if "youtube.com" in channel_input:
                if "/channel/" in channel_input:
                    return channel_input.split("/channel/")[1].split("/")[0]
                elif "/@" in channel_input:
                    handle = channel_input.split("/@")[1].split("/")[0]
                    # 핸들로 채널 ID 검색
                    response = self.youtube.search().list(
                        q=f"@{handle}",
                        part="snippet",
                        type="channel",
                        maxResults=1
                    ).execute()
                    if response.get("items"):
                        return response["items"][0]["snippet"]["channelId"]
            
            # @핸들 형식 처리
            elif channel_input.startswith("@"):
                handle = channel_input[1:]
                response = self.youtube.search().list(
                    q=f"@{handle}",
                    part="snippet",
                    type="channel",
                    maxResults=1
                ).execute()
                if response.get("items"):
                    return response["items"][0]["snippet"]["channelId"]
            
            # 채널 ID 형식 처리
            elif re.match(r'^UC[\w-]{21}[AQgw]$', channel_input):
                return channel_input
            
            # 채널명으로 검색 (가장 일반적인 경우)
            else:
                print(f"채널명으로 검색 중: {channel_input}")
                response = self.youtube.search().list(
                    q=channel_input,
                    part="snippet",
                    type="channel",
                    maxResults=5
                ).execute()
                
                if response.get("items"):
                    # 정확히 일치하는 채널명이 있는지 확인
                    for item in response["items"]:
                        if item["snippet"]["title"].lower() == channel_input.lower():
                            print(f"정확히 일치하는 채널 발견: {item['snippet']['title']}")
                            return item["snippet"]["channelId"]
                    
                    # 정확히 일치하는 것이 없으면 첫 번째 결과 사용
                    first_result = response["items"][0]
                    print(f"첫 번째 검색 결과 사용: {first_result['snippet']['title']}")
                    return first_result["snippet"]["channelId"]
            
            return None

        except HttpError as e:
            print(f"YouTube API 오류: {e}")
            if e.resp.status == 403:  # Quota exceeded
                print("API 할당량 초과. 다음 키로 전환 중...")
                self._switch_api_key()
                return self._extract_channel_id(channel_input)
            return None
        except Exception as e:
            print(f"채널 ID 추출 중 오류: {str(e)}")
            return None

    def search_videos(self, query: str, max_results: int = 50) -> List[Dict]:
        """키워드로 비디오를 검색합니다."""
        try:
            search_response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                type="video"
            ).execute()

            videos = []
            for item in search_response.get("items", []):
                video_data = {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_id": item["snippet"]["channelId"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video_data)
            return videos

        except HttpError as e:
            if e.resp.status == 403:  # Quota exceeded
                self._switch_api_key()
                return self.search_videos(query, max_results)
            raise e

    def get_channel_info(self, channel_id: str) -> Dict:
        """채널 정보를 가져옵니다."""
        try:
            response = self.youtube.channels().list(
                part="snippet",
                id=channel_id
            ).execute()
            
            if response.get("items"):
                channel_info = response["items"][0]["snippet"]
                return {
                    "channel_id": channel_id,
                    "channel_title": channel_info["title"],
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}"
                }
            return {}
        except Exception as e:
            print(f"채널 정보 가져오기 실패: {str(e)}")
            return {}

    def get_channel_videos(self, channel_input: str, max_results: int = 50) -> List[Dict]:
        """채널의 최근 비디오를 가져옵니다."""
        channel_id = self._extract_channel_id(channel_input)
        if not channel_id:
            print(f"Could not find channel ID for input: {channel_input}")
            return []

        try:
            # 채널 정보 가져오기
            channel_info_response = self.youtube.channels().list(
                part="snippet,contentDetails",
                id=channel_id
            ).execute()

            if not channel_info_response.get("items"):
                return []

            channel_title = channel_info_response["items"][0]["snippet"]["title"]
            uploads_playlist_id = channel_info_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # 재생목록의 비디오 가져오기
            playlist_response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()

            videos = []
            for item in playlist_response.get("items", []):
                video_data = {
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "published_at": item["snippet"]["publishedAt"],
                    "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
                }
                videos.append(video_data)
            return videos

        except HttpError as e:
            if e.resp.status == 403:  # Quota exceeded
                self._switch_api_key()
                return self.get_channel_videos(channel_input, max_results)
            raise e

    def get_video_captions(self, video_id: str) -> Optional[str]:
        """비디오의 자막을 가져옵니다. (수동 자막 우선, 없으면 자동 생성 자막 사용)"""
        try:
            # YouTube Transcript API를 사용하여 자막 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            transcript_type = ""
            
            # 1단계: 수동 한국어 자막 시도
            try:
                transcript = transcript_list.find_manually_created_transcript(['ko'])
                transcript_type = "수동 한국어"
            except:
                # 2단계: 수동 영어 자막 시도
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                    transcript_type = "수동 영어"
                except:
                    # 3단계: 자동 생성 한국어 자막 시도
                    try:
                        transcript = transcript_list.find_generated_transcript(['ko'])
                        transcript_type = "자동 생성 한국어"
                    except:
                        # 4단계: 자동 생성 영어 자막 시도
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                            transcript_type = "자동 생성 영어"
                        except:
                            # 5단계: 어떤 자막이든 가져오기 (최후의 수단)
                            try:
                                available_transcripts = list(transcript_list)
                                if available_transcripts:
                                    transcript = available_transcripts[0]
                                    transcript_type = f"사용 가능한 자막 ({transcript.language_code})"
                                else:
                                    print(f"비디오 {video_id}에 자막이 전혀 없습니다.")
                                    return None
                            except:
                                print(f"비디오 {video_id}에서 자막을 찾을 수 없습니다.")
                                return None

            # 자막 가져오기
            transcript_data = transcript.fetch()
            
            # 자막을 텍스트로 변환
            formatter = TextFormatter()
            captions = formatter.format_transcript(transcript_data)
            
            print(f"비디오 {video_id}의 자막을 성공적으로 가져왔습니다. ({transcript_type}, 길이: {len(captions)} 문자)")
            return captions

        except Exception as e:
            print(f"자막 가져오기 실패: {str(e)}")
            return None

    def get_videos(self, input_str: str, is_keyword: bool = False, max_results: int = 50) -> List[Dict]:
        """채널 또는 키워드로 비디오를 가져옵니다."""
        if is_keyword:
            return self.search_videos(input_str, max_results)
        else:
            return self.get_channel_videos(input_str, max_results) 