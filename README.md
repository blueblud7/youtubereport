# YouTube 리포트 생성기

이 프로젝트는 YouTube 채널이나 키워드를 기반으로 자동으로 리포트를 생성하는 시스템입니다.

## 주요 기능

- YouTube 채널 모니터링
- 키워드 기반 비디오 검색
- 자막 기반 콘텐츠 분석
- GPT-4를 이용한 인사이트 추출
- 일일 리포트 자동 생성

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. API 키 설정:
```bash
# config_template.py를 config.py로 복사
cp config_template.py config.py

# 환경변수 설정 (macOS/Linux)
export YOUTUBE_API_KEYS="your_youtube_api_key1,your_youtube_api_key2,your_youtube_api_key3"
export OPENAI_API_KEY="your_openai_api_key"

# 또는 .env 파일 생성
echo "YOUTUBE_API_KEYS=your_youtube_api_key1,your_youtube_api_key2" > .env
echo "OPENAI_API_KEY=your_openai_api_key" >> .env
```

### API 키 발급 방법

**YouTube Data API v3:**
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. API 키 생성

**OpenAI API:**
1. [OpenAI Platform](https://platform.openai.com/) 회원가입
2. API Keys 섹션에서 새 API 키 생성

## 사용 방법

### 웹 애플리케이션 실행 (권장)

1. Flask 웹 서버 실행:
```bash
python app.py
```

2. 브라우저에서 `http://localhost:3000` 접속

3. 웹 인터페이스에서:
   - 채널명 또는 키워드 추가
   - 프롬프트 스타일 선택 (간단함/전문적/요약/커스텀)
   - 리포트 생성 및 확인
   - 마크다운 렌더링된 리포트 보기
   - 참고문헌 링크를 통한 YouTube 비디오 바로가기

### 명령줄 실행

1. 채널 ID나 키워드 설정:
- `main.py` 파일의 `channels`와 `keywords` 리스트에 모니터링하고 싶은 채널 ID와 키워드를 추가합니다.

2. 리포트 생성 실행:
```bash
python main.py
```

3. 생성된 리포트 확인:
- `reports` 디렉토리에서 생성된 리포트를 확인할 수 있습니다.
- 리포트는 채널/키워드별로 날짜가 포함된 파일명으로 저장됩니다.

## 리포트 형식

생성되는 리포트는 다음과 같은 형식을 포함합니다:

1. **오늘의 주요 트렌드**
2. **핵심 이슈 및 인사이트**
3. **주목할 만한 콘텐츠**
4. **향후 전망**
5. **참고문헌** - 분석된 YouTube 비디오 링크

### 프롬프트 스타일 옵션

- **간단함**: 핵심 내용만 간결하게
- **전문적**: 상세한 분석과 전문적 표현
- **요약**: 불릿 포인트 형태의 요약
- **커스텀**: 사용자 정의 프롬프트, 언어, 단어 수 설정

## 주요 특징

- **다단계 자막 처리**: 수동 자막 → 자동 생성 자막 순으로 시도
- **다중 API 키 지원**: YouTube API 할당량 소진 시 자동 전환
- **마크다운 렌더링**: 웹에서 보기 좋은 리포트 제공
- **참고문헌 자동 생성**: 분석된 YouTube 비디오 링크 포함
- **프롬프트 커스터마이징**: 4가지 스타일 + 사용자 정의

## 주의사항

- YouTube API 할당량이 소진되면 자동으로 다음 API 키로 전환됩니다.
- 수동 자막이 없는 경우 자동 생성 자막을 사용합니다.
- GPT-4o-mini API 사용량에 따라 비용이 발생할 수 있습니다.
- **config.py 파일은 절대 깃헙에 커밋하지 마세요** (API 키 포함). 