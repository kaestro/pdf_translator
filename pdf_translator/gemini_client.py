"""
Gemini API 클라이언트 모듈

이 모듈은 Google의 Gemini API와 상호작용하는 클라이언트 클래스를 제공합니다.
환경 변수에서 API 키를 로드하고 Gemini 모델에 텍스트를 보내 번역 결과를 얻습니다.
"""

import os
import base64
from typing import Optional, Dict, Any, Union, BinaryIO
import google.generativeai as genai
from dotenv import load_dotenv
from .gemini_models import GeminiModel

class GeminiClient:
    """
    Gemini API를 사용하기 위한 클라이언트 클래스
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        GeminiClient 초기화
        
        Args:
            api_key: Gemini API 키. 제공되지 않으면 환경 변수에서 로드합니다.
            model_name: 사용할 Gemini 모델 이름. 제공되지 않으면 기본 모델을 사용합니다.
        """
        # 환경 변수에서 API 키 로드
        load_dotenv()
        
        # API 키 설정
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API 키가 필요합니다. 환경 변수 GEMINI_API_KEY를 설정하거나 API 키를 직접 전달하세요.")
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        
        # 모델 설정
        self.text_model_id = model_name if model_name else GeminiModel.GEMINI_1_5_FLASH.value
        self.vision_model_id = GeminiModel.GEMINI_1_5_FLASH.value
        self.text_model = genai.GenerativeModel(self.text_model_id)
        self.vision_model = genai.GenerativeModel(self.vision_model_id)
    
    def translate_text_only(self, text: str, target_language: str = "한국어") -> str:
        """
        텍스트를 대상 언어로 번역합니다.
        
        Args:
            text: 번역할 텍스트
            target_language: 번역할 대상 언어 (기본값: 한국어)
            
        Returns:
            번역된 텍스트
        """
        prompt = f"""다음 텍스트를 {target_language}로 번역해주세요. 
        원본 텍스트의 의미와 맥락을 정확하게 유지하면서 자연스러운 {target_language}로 번역하세요.
        
        원본 텍스트:
        {text}
        """
        
        response = self.text_model.generate_content(prompt)
        
        # 응답 확인 및 반환
        if hasattr(response, 'text'):
            return response.text
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다.")
    
    def translate(self, content: Union[str, bytes, BinaryIO], target_language: str = "한국어", text_only: bool = False) -> str:
        """
        텍스트 또는 이미지를 대상 언어로 번역합니다.
        
        Args:
            content: 번역할 텍스트 또는 이미지 데이터
            target_language: 번역할 대상 언어 (기본값: 한국어)
            text_only: 텍스트만 처리할지 여부 (기본값: False)
            
        Returns:
            번역된 텍스트
        """
        if text_only or isinstance(content, str):
            return self.translate_text_only(content if isinstance(content, str) else content.decode('utf-8'), target_language)
        
        # 이미지 데이터 처리
        prompt = f"""다음 이미지에 있는 모든 텍스트를 {target_language}로 번역해주세요.
        원본 텍스트의 의미와 맥락을 정확하게 유지하면서 자연스러운 {target_language}로 번역하세요.
        번역된 텍스트만 제공해주세요. 원본 텍스트는 포함하지 마세요.
        """
        
        # 이미지 데이터 준비
        if isinstance(content, bytes):
            image_data = content
        elif hasattr(content, 'read'):
            image_data = content.read()
        else:
            raise ValueError("지원되지 않는 콘텐츠 형식입니다.")
        
        # 멀티모달 요청 생성
        response = self.vision_model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        # 응답 확인 및 반환
        if hasattr(response, 'text'):
            return response.text
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다.")
    
    def translate_to_markdown(self, content: Union[str, bytes, BinaryIO], target_language: str = "한국어", page_num: int = 1, image_tag: Optional[str] = None) -> str:
        """
        텍스트 또는 이미지를 대상 언어로 번역하고 마크다운 형식으로 포맷팅하여 반환합니다.
        
        Args:
            content: 번역할 텍스트 또는 이미지 데이터
            target_language: 번역할 대상 언어 (기본값: 한국어)
            page_num: 페이지 번호 (기본값: 1)
            image_tag: 이미지에 대한 태그 (이미지가 있는 경우 제공)
            
        Returns:
            마크다운 형식으로 포맷팅된 번역 텍스트
        """
        if isinstance(content, str):
            return self.translate_text_to_markdown(content, target_language, page_num)
        
        # 이미지 데이터 처리
        prompt = f"""다음 이미지에 있는 모든 텍스트를 {target_language}로 번역하고, 결과를 마크다운 형식으로 제공해주세요.

        <번역 및 마크다운 형식 지침>
        1. 원본 텍스트의 의미와 맥락을 정확하게 유지하면서 자연스러운 {target_language}로 번역하세요.
        2. 결과는 마크다운 형식을 사용해야 합니다.
        3. 적절한 마크다운 요소(제목, 강조, 목록, 인용 등)를 사용하여 원본 문서의 구조를 최대한 유지하세요.
        4. 문서 내 실제 이미지(그림, 다이어그램, 차트 등)가 있는 경우에만 다음 형식의 이미지 태그를 삽입하세요: ![이미지 설명](IMAGE_{page_num}_그림번호)
        5. 중요: 전체 페이지 자체에 대한 이미지 태그는 포함하지 마세요. PDF 페이지 전체를 참조하는 이미지 태그는 필요하지 않습니다.
        6. 표나 차트가 있는 경우 마크다운 테이블 형식으로 변환하세요.
        7. 응답은 순수한 마크다운 형식으로만 제공하세요. 다른 설명이나 주석은 포함하지 마세요.
        8. 여기서 보이는 이미지는 PDF 페이지 전체를 스캔한 것이므로, 페이지 자체에 대한 이미지 참조는 불필요합니다.
        
        지금은 페이지 {page_num}을(를) 번역 중입니다.
        """
        
        # 이미지 데이터 준비
        if isinstance(content, bytes):
            image_data = content
        elif hasattr(content, 'read'):
            image_data = content.read()
        else:
            raise ValueError("지원되지 않는 콘텐츠 형식입니다.")
        
        # 멀티모달 요청 생성
        response = self.vision_model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        # 응답 확인 및 반환
        if hasattr(response, 'text'):
            markdown_text = response.text.strip()
            
            # 이미지 태그가 제공된 경우 이미지 참조 업데이트
            if image_tag:
                # 이미지 태그 패턴 찾아서 대체
                import re
                pattern = r'!\[([^\]]*)\]\(IMAGE_' + str(page_num) + r'(?:_\d+)?\)'
                
                # 이미지 태그 디렉토리 경로
                image_dir = os.path.dirname(image_tag)
                image_base = os.path.basename(image_tag)
                
                # 그림 번호에 따라 이미지 파일명 생성
                def replace_image_tag(match):
                    alt_text = match.group(1)
                    
                    # 그림 번호가 있는 경우 추출
                    fig_pattern = r'IMAGE_' + str(page_num) + r'_(\d+)'
                    fig_match = re.search(fig_pattern, match.group(0))
                    
                    if fig_match:
                        fig_num = fig_match.group(1)
                        image_name = image_base.replace('.png', f'_fig_{fig_num}.png')
                    else:
                        image_name = image_base
                        
                    return f'![{alt_text}]({os.path.join(image_dir, image_name)})'
                
                # 이미지 태그 대체
                markdown_text = re.sub(pattern, replace_image_tag, markdown_text)
            
            return markdown_text
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다.")
    
    def translate_text_to_markdown(self, text: str, target_language: str = "한국어", page_num: int = 1) -> str:
        """
        텍스트를 대상 언어로 번역하고 마크다운 형식으로 포맷팅하여 반환합니다.
        
        Args:
            text: 번역할 텍스트
            target_language: 번역할 대상 언어 (기본값: 한국어)
            page_num: 페이지 번호 (기본값: 1)
            
        Returns:
            마크다운 형식으로 포맷팅된 번역 텍스트
        """
        prompt = f"""다음 텍스트를 {target_language}로 번역하고, 결과를 마크다운 형식으로 제공해주세요.
        
        <번역 및 마크다운 형식 지침>
        1. 원본 텍스트의 의미와 맥락을 정확하게 유지하면서 자연스러운 {target_language}로 번역하세요.
        2. 결과는 마크다운 형식을 사용해야 합니다.
        3. 적절한 마크다운 요소(제목, 강조, 목록, 인용 등)를 사용하여 원본 문서의 구조를 최대한 유지하세요.
        4. 표나 차트가 있는 경우 마크다운 테이블 형식으로 변환하세요.
        5. 응답은 순수한 마크다운 형식으로만 제공하세요. 다른 설명이나 주석은 포함하지 마세요.
        
        지금은 페이지 {page_num}을(를) 번역 중입니다.
        
        원본 텍스트:
        {text}
        """
        
        response = self.text_model.generate_content(prompt)
        
        # 응답 확인 및 반환
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다.")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        사용 가능한 모델 정보를 반환합니다.
        
        Returns:
            모델 정보를 포함하는 딕셔너리
        """
        models = genai.list_models()
        return {model.name: model.supported_generation_methods for model in models}
    
    def get_available_models(self) -> Dict[str, str]:
        """
        사용 가능한 모든 Gemini 모델 목록을 반환합니다.
        
        Returns:
            모델 이름: 모델 ID 딕셔너리
        """
        return {model.name: model.value for model in GeminiModel} 