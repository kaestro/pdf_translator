"""
PDF 처리 모듈

PDF 파일을 읽고 텍스트를 추출하는 기능을 제공합니다.
"""

import os
import io
from typing import List, Tuple, Optional, BinaryIO
import PyPDF2
import fitz  # PyMuPDF
from tqdm import tqdm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
    
    def extract_page_images(self, pdf_path: str) -> List[Tuple[int, bytes]]:
        """
        PDF 파일에서 각 페이지를 이미지로 추출합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            (페이지 번호, 이미지 데이터) 튜플의 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        extracted_images = []
        
        pdf_document = fitz.open(pdf_path)
        for page_num, page in enumerate(pdf_document):
            # 페이지를 이미지로 렌더링 (해상도 300dpi)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_data = pix.tobytes("png")
            extracted_images.append((page_num + 1, img_data))
        
        pdf_document.close()
        return extracted_images
    
    def translate_text_only(self, pdf_path: str, output_path: str = None, target_language: str = "한국어") -> List[Tuple[int, str, str]]:
        """
        PDF 파일의 텍스트만 추출하여 번역합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            output_path: 번역 결과를 저장할 파일 경로. 제공되지 않으면 결과만 반환합니다.
            target_language: 번역할 대상 언어 (기본값: 한국어)
            
        Returns:
            (페이지 번호, 원본 텍스트, 번역된 텍스트) 튜플의 리스트
        """
        extracted_text = self.extract_text_from_pdf(pdf_path)
        translated_results = []
        
        print(f"PDF 텍스트 번역 중... ({len(extracted_text)}페이지)")
        
        for page_num, text in tqdm(extracted_text, desc="번역 중"):
            translated_text = self.gemini_client.translate_text_only(text, target_language)
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
    
    def translate(self, pdf_path: str, output_path: Optional[str] = None, target_language: str = "한국어", text_only: bool = False) -> List[Tuple[int, str]]:
        """
        PDF 파일을 번역합니다. 
        text_only가 False이면 멀티모달 방식으로 페이지 이미지를 전송하여 번역합니다.
        text_only가 True이면 텍스트만 추출하여 번역합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            output_path: 번역 결과를 저장할 PDF 파일 경로. 제공되지 않으면 결과만 반환합니다.
            target_language: 번역할 대상 언어 (기본값: 한국어)
            text_only: 텍스트만 추출하여 번역할지 여부 (기본값: False)
            
        Returns:
            (페이지 번호, 번역된 텍스트) 튜플의 리스트
        """
        if text_only:
            results = self.translate_text_only(pdf_path, output_path, target_language)
            return [(page_num, translated) for page_num, _, translated in results]
        
        # 멀티모달 번역 수행
        extracted_images = self.extract_page_images(pdf_path)
        translated_results = []
        
        print(f"PDF 멀티모달 번역 중... ({len(extracted_images)}페이지)")
        
        for page_num, img_data in tqdm(extracted_images, desc="번역 중"):
            translated_text = self.gemini_client.translate(img_data, target_language)
            translated_results.append((page_num, translated_text))
        
        # 번역 결과를 PDF로 저장
        if output_path:
            self._create_translated_pdf(translated_results, output_path)
            print(f"번역된 PDF가 저장되었습니다: {output_path}")
        
        return translated_results
    
    def _create_translated_pdf(self, translated_results: List[Tuple[int, str]], output_path: str):
        """
        번역 결과를 PDF 파일로 생성합니다.
        
        Args:
            translated_results: (페이지 번호, 번역된 텍스트) 튜플의 리스트
            output_path: 저장할 PDF 파일 경로
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        for _, text in sorted(translated_results):
            # 페이지 설정
            c.setFont("Helvetica", 10)
            
            # 텍스트 추가
            text_object = c.beginText(40, height - 40)
            text_object.setFont("Helvetica", 10)
            
            # 텍스트 줄바꿈 처리
            for line in text.split('\n'):
                # 긴 줄 분리
                for i in range(0, len(line), 80):
                    chunk = line[i:i+80]
                    if chunk:
                        text_object.textLine(chunk)
            
            c.drawText(text_object)
            c.showPage()
        
        c.save()
        
        # 파일로 저장
        buffer.seek(0)
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue()) 