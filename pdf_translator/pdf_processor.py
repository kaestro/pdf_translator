"""
PDF 처리 모듈

PDF 파일을 읽고 텍스트를 추출하는 기능을 제공합니다.
"""

import os
from typing import List, Tuple
import PyPDF2
from tqdm import tqdm
from .gemini_client import GeminiClient

class PDFProcessor:
    """
    PDF 파일 처리를 위한 클래스
    """
    
    def __init__(self, gemini_client: GeminiClient = None):
        """
        PDFProcessor 초기화
        
        Args:
            gemini_client: Gemini API 클라이언트. 제공되지 않으면 새로 생성합니다.
        """
        self.gemini_client = gemini_client or GeminiClient()
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        PDF 파일에서 텍스트를 추출합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            (페이지 번호, 텍스트) 튜플의 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        extracted_text = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text:
                    extracted_text.append((page_num + 1, text))
        
        return extracted_text
    
    def translate_pdf(self, pdf_path: str, output_path: str = None, target_language: str = "한국어") -> List[Tuple[int, str, str]]:
        """
        PDF 파일을 번역합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            output_path: 번역 결과를 저장할 파일 경로. 제공되지 않으면 결과만 반환합니다.
            target_language: 번역할 대상 언어 (기본값: 한국어)
            
        Returns:
            (페이지 번호, 원본 텍스트, 번역된 텍스트) 튜플의 리스트
        """
        extracted_text = self.extract_text_from_pdf(pdf_path)
        translated_results = []
        
        print(f"PDF 번역 중... ({len(extracted_text)}페이지)")
        
        for page_num, text in tqdm(extracted_text, desc="번역 중"):
            translated_text = self.gemini_client.translate(text, target_language)
            translated_results.append((page_num, text, translated_text))
        
        # 결과를 파일로 저장
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as file:
                for page_num, source, translated in translated_results:
                    file.write(f"=== 페이지 {page_num} ===\n\n")
                    file.write("원본:\n")
                    file.write(f"{source}\n\n")
                    file.write("번역:\n")
                    file.write(f"{translated}\n\n")
                    file.write("-" * 80 + "\n\n")
            
            print(f"번역 결과가 저장되었습니다: {output_path}")
        
        return translated_results 