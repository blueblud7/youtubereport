from openai import OpenAI
from config import OPENAI_API_KEY

class GPTService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def get_prompt_by_type(self, prompt_type: str, language: str = 'ko', word_count: int = 500, custom_prompt: str = None) -> str:
        """프롬프트 타입에 따른 시스템 프롬프트를 반환합니다."""
        language_map = {
            'ko': '한국어',
            'en': 'English',
            'ja': '日本語',
            'zh': '中文'
        }
        
        lang_instruction = f"반드시 {language_map.get(language, '한국어')}로 답변해주세요."
        word_instruction = f"답변은 약 {word_count}자 내외로 작성해주세요."
        
        prompts = {
            'simple': f"""당신은 YouTube 콘텐츠를 간결하게 요약하는 전문가입니다. 
{lang_instruction} {word_instruction}
핵심 내용만 간략하게 정리하여 이해하기 쉽게 전달해주세요.""",
            
            'professional': f"""당신은 전문적인 미디어 분석 리포트를 작성하는 전문가입니다.
{lang_instruction} {word_instruction}
상세한 분석과 인사이트를 포함한 전문적인 리포트 형식으로 작성해주세요. 
다음 구성을 포함해주세요: 1) 요약, 2) 주요 내용 분석, 3) 시사점, 4) 결론.""",
            
            'bullet': f"""당신은 정보를 체계적으로 정리하는 전문가입니다.
{lang_instruction} {word_instruction}
모든 내용을 불릿 포인트 형식으로 구조화하여 정리해주세요.
• 주요 항목별로 분류
• 핵심 포인트 요약
• 읽기 쉬운 구조로 작성""",
            
            'custom': custom_prompt if custom_prompt else f"""당신은 YouTube 콘텐츠 분석 전문가입니다.
{lang_instruction} {word_instruction}
주어진 내용을 분석하여 유용한 리포트를 작성해주세요."""
        }
        
        return prompts.get(prompt_type, prompts['simple'])

    def analyze_content(self, content: str, prompt_type: str = 'simple', language: str = 'ko', word_count: int = 500, custom_prompt: str = None) -> str:
        """콘텐츠를 분석하고 요약합니다."""
        try:
            system_prompt = self.get_prompt_by_type(prompt_type, language, word_count, custom_prompt)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 YouTube 비디오 콘텐츠를 분석해주세요:\n\n{content}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Content analysis failed: {str(e)}")
            return ""

    def generate_daily_report(self, analyses: list, prompt_type: str = 'simple', language: str = 'ko', word_count: int = 500, custom_prompt: str = None, references: list = None) -> str:
        """일일 리포트를 생성합니다."""
        try:
            system_prompt = self.get_prompt_by_type(prompt_type, language, word_count, custom_prompt)
            combined_analyses = "\n\n".join(analyses)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 분석 결과들을 종합하여 일일 리포트를 작성해주세요:\n\n{combined_analyses}"}
                ]
            )
            
            report_content = response.choices[0].message.content
            
            # 참고문헌 추가
            if references:
                report_content += self._format_references(references, language)
            
            return report_content
        except Exception as e:
            print(f"Report generation failed: {str(e)}")
            return ""
    
    def _format_references(self, references: list, language: str = 'ko') -> str:
        """참고문헌을 포맷합니다."""
        if not references:
            return ""
        
        # 언어에 따른 제목 설정
        if language == 'ko':
            ref_title = "\n\n참고문헌"
        elif language == 'en':
            ref_title = "\n\nReferences"
        elif language == 'ja':
            ref_title = "\n\n参考文献"
        elif language == 'zh':
            ref_title = "\n\n参考文献"
        else:
            ref_title = "\n\n참고문헌"
        
        ref_content = ref_title + "\n"
        
        # 단순한 번호 목록으로 비디오 나열
        for i, video in enumerate(references, 1):
            url = video.get('url', '')
            ref_content += f"{i}. {url}\n"
        
        return ref_content 