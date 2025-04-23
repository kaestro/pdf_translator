"""
PDF 처리 모듈

PDF 파일을 읽고 텍스트를 추출하는 기능을 제공합니다.
"""

import os
import io
import tempfile
from typing import List, Tuple, Optional, BinaryIO, Dict, Any
import PyPDF2
import fitz  # PyMuPDF
from tqdm import tqdm
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import PIL
from .gemini_client import GeminiClient
import re
from reportlab.lib import colors
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.platypus import Table, TableStyle
import textwrap

# OS별 한국어 폰트 경로와 이름 정의
FONT_CONFIG: Dict[str, Dict[str, str]] = {
    "windows": {
        "path": "C:/Windows/Fonts/malgun.ttf",
        "name": "MalgunGothic"
    },
    "macos": {
        "path": "/Library/Fonts/AppleGothic.ttf",
        "name": "AppleGothic"
    },
    "linux": {
        "path": "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "name": "NanumGothic"
    },
    "default": {
        "path": "",
        "name": "Helvetica"  # Helvetica는 ReportLab 기본 폰트, 등록 불필요
    }
}

def _register_korean_font() -> bool:
    """
    운영체제에 따라 적절한 한국어 폰트를 등록합니다.
    
    Returns:
        등록 성공 여부
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 환경 변수에서 OS 정보 가져오기
    current_os = os.getenv("CURRENT_OS", "").lower()
    
    # OS 환경변수가 비어있으면 자동 감지 시도
    if not current_os:
        # 자동 OS 감지
        if os.name == 'nt':
            current_os = "windows"
        elif os.name == 'posix':
            # macOS와 Linux 구분
            if os.uname().sysname == 'Darwin':
                current_os = "macos"
            else:
                current_os = "linux"
        else:
            current_os = "default"
        
        print(f"OS 자동 감지: {current_os}")
    
    # OS에 맞는 폰트 설정 가져오기
    font_config = FONT_CONFIG.get(current_os, FONT_CONFIG["default"])
    font_path = font_config["path"]
    font_name = font_config["name"]
    
    # 기본 폰트인 경우 등록 필요 없음
    if current_os == "default" or font_name == "Helvetica":
        print("기본 폰트(Helvetica)를 사용합니다. 한국어 표시가 제한될 수 있습니다.")
        return False
    
    # 폰트 파일 존재 여부 확인
    if not os.path.exists(font_path):
        print(f"경고: 폰트 파일을 찾을 수 없습니다: {font_path}")
        print("기본 폰트(Helvetica)를 사용합니다. 한국어 표시가 제한될 수 있습니다.")
        return False
    
    try:
        # 폰트 등록
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        print(f"폰트 등록 성공: {font_name} ({font_path})")
        return True
    except Exception as e:
        print(f"폰트 등록 실패: {e}")
        print("경고: 한국어 폰트를 등록할 수 없습니다. 기본 폰트(Helvetica)를 사용합니다.")
        return False

# 글로벌 폰트 등록 시도
font_registered = _register_korean_font()

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
    
    def extract_page_elements(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDF 파일에서 각 페이지의 이미지와 텍스트 요소를 추출합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            페이지 정보와 요소 목록을 포함한 딕셔너리 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        pages_elements = []
        
        # PyMuPDF를 사용하여 PDF 열기
        pdf_document = fitz.open(pdf_path)
        
        # 임시 디렉토리 생성 (이미지 저장용)
        temp_dir = tempfile.mkdtemp()
        
        try:
            for page_num, page in enumerate(pdf_document):
                page_elements = {
                    "page_num": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "images": [],
                    "text": page.get_text(),
                    "page_image": None,  # 페이지 전체 이미지
                }
                
                # 페이지 전체 이미지 (멀티모달 번역용)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                page_elements["page_image"] = pix.tobytes("png")
                
                # 페이지에서 개별 이미지 추출
                image_list = page.get_images(full=True)
                
                # 이미지가 있는 경우 각 이미지 처리
                for img_idx, img_info in enumerate(image_list):
                    # 이미지 정보 추출
                    xref = img_info[0]  # 이미지 참조 번호
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # 이미지의 위치와 크기 찾기
                    image_rect = None
                    for item in page.get_images(full=True):
                        if item[0] == xref:
                            for rect in page.get_image_rects(item):
                                image_rect = rect
                                break
                    
                    if image_rect:
                        image_element = {
                            "index": img_idx,
                            "xref": xref,
                            "bytes": image_bytes,
                            "rect": {
                                "x0": image_rect.x0,
                                "y0": image_rect.y0,
                                "x1": image_rect.x1,
                                "y1": image_rect.y1,
                                "width": image_rect.width,
                                "height": image_rect.height,
                            },
                            "extension": base_image["ext"],
                        }
                        page_elements["images"].append(image_element)
                
                pages_elements.append(page_elements)
            
            return pages_elements
            
        finally:
            # PDF 파일 닫기
            pdf_document.close()
            
            # 임시 디렉토리 정리 (필요한 경우)
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
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
    
    def translate(self, pdf_path: str, output_path: Optional[str] = None, target_language: str = "한국어", text_only: bool = False, preserve_layout: bool = True) -> List[Tuple[int, str]]:
        """
        PDF 파일을 번역합니다. 
        text_only가 False이면 멀티모달 방식으로 페이지 이미지를 전송하여 번역합니다.
        text_only가 True이면 텍스트만 추출하여 번역합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            output_path: 번역 결과를 저장할 PDF 파일 경로. 제공되지 않으면 결과만 반환합니다.
            target_language: 번역할 대상 언어 (기본값: 한국어)
            text_only: 텍스트만 추출하여 번역할지 여부 (기본값: False)
            preserve_layout: 원본 레이아웃을 최대한 보존할지 여부 (기본값: True)
            
        Returns:
            (페이지 번호, 번역된 텍스트) 튜플의 리스트
        """
        if text_only:
            results = self.translate_text_only(pdf_path, output_path, target_language)
            return [(page_num, translated) for page_num, _, translated in results]
        
        # 멀티모달 번역 수행
        print(f"PDF 요소 추출 중...")
        pages_elements = self.extract_page_elements(pdf_path)
        translated_results = []
        
        print(f"PDF 멀티모달 번역 중... ({len(pages_elements)}페이지)")
        
        for page_elements in tqdm(pages_elements, desc="번역 중"):
            page_num = page_elements["page_num"]
            img_data = page_elements["page_image"]
            
            # 페이지 이미지를 사용하여 멀티모달 번역 수행
            translated_text = self.gemini_client.translate(img_data, target_language)
            translated_results.append((page_num, translated_text, page_elements))
        
        # 번역 결과를 PDF로 저장
        if output_path:
            if preserve_layout:
                # 원본 레이아웃을 유지하는 PDF 생성
                self._create_layout_preserved_pdf(pdf_path, translated_results, output_path)
            else:
                # 기존 방식으로 PDF 생성
                self._create_translated_pdf_with_images(translated_results, output_path)
            print(f"번역된 PDF가 저장되었습니다: {output_path}")
        
        return [(page_num, translated) for page_num, translated, _ in translated_results]
    
    def _create_translated_pdf_with_images(self, translated_results: List[Tuple[int, str, Dict[str, Any]]], output_path: str):
        """
        번역 결과와 원본 이미지를 포함한 PDF 파일을 생성합니다.
        
        Args:
            translated_results: (페이지 번호, 번역된 텍스트, 페이지 요소) 튜플의 리스트
            output_path: 저장할 PDF 파일 경로
        """
        buffer = io.BytesIO()
        
        # 글로벌 font_registered 변수 사용
        global font_registered
        
        # 환경 변수 로드
        load_dotenv()
        current_os = os.getenv("CURRENT_OS", "").lower()
        
        # OS 자동 감지
        if not current_os:
            if os.name == 'nt':
                current_os = "windows"
            elif os.name == 'posix':
                if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
                    current_os = "macos"
                else:
                    current_os = "linux"
            else:
                current_os = "default"
        
        # OS에 맞는 폰트 설정 가져오기
        font_config = FONT_CONFIG.get(current_os, FONT_CONFIG["default"])
        font_name = font_config["name"]
        
        # PDF 문서 설정
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # 제목 스타일 설정
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading2'],
            alignment=TA_LEFT
        )
        if font_registered and font_name != "Helvetica":
            title_style.fontName = font_name
        
        # 본문 스타일 설정 (한글 폰트 적용)
        korean_style = ParagraphStyle(
            name='KoreanStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14  # 줄 간격 설정
        )
        if font_registered and font_name != "Helvetica":
            korean_style.fontName = font_name
        
        # 전체 스토리 및 임시 파일 목록 초기화
        story = []
        temp_files = []
        
        try:
            # 각 페이지 처리
            for page_num, text, page_elements in sorted(translated_results):
                # 페이지 구분 추가
                if page_num > 1:
                    story.append(PageBreak())
                
                # 페이지 번호 추가
                page_header = Paragraph(f"=== 페이지 {page_num} ===", title_style)
                story.append(page_header)
                story.append(Spacer(1, 0.2 * cm))
                
                # 원본 이미지 추가
                page_images = page_elements.get("images", [])
                if page_images:
                    for img_info in page_images:
                        try:
                            # 이미지 데이터로부터 reportlab 이미지 생성
                            img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{img_info["extension"]}')
                            img_temp.write(img_info["bytes"])
                            img_temp.close()
                            
                            # 임시 파일 경로 저장
                            temp_files.append(img_temp.name)
                            
                            # 원본 이미지의 크기 비율을 유지하며 적절한 크기로 조정
                            img_width = img_info["rect"]["width"]
                            img_height = img_info["rect"]["height"]
                            
                            # 페이지 폭에 맞게 이미지 크기 조정
                            available_width = doc.width
                            if img_width > available_width:
                                scale_factor = available_width / img_width
                                img_width = available_width
                                img_height = img_height * scale_factor
                            
                            # 이미지 추가
                            img = Image(img_temp.name, width=img_width, height=img_height)
                            story.append(img)
                            story.append(Spacer(1, 0.3 * cm))
                            
                        except Exception as e:
                            print(f"이미지 추가 중 오류 발생: {e}")
                            # 오류 발생 시 계속 진행
                            continue
                
                # 텍스트를 Paragraph 객체로 변환 (자동 줄바꿈 처리)
                paragraph_text = text.replace('\n', '<br/>')
                p = Paragraph(paragraph_text, korean_style)
                story.append(p)
                
                # 페이지 구분을 위한 간격 추가
                story.append(Spacer(1, 0.5 * cm))
            
            # PDF 빌드
            doc.build(story)
            
            # 파일로 저장
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
                
            print(f"번역된 PDF가 저장되었습니다: {output_path}")
            
        except Exception as e:
            print(f"PDF 빌드 중 오류 발생: {e}")
            print(f"폰트 설정: {font_name} (등록 성공: {font_registered})")
            # 오류 발생해도 buffer에 부분적으로 쓰여진 내용이 있을 수 있음
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            print(f"오류에도 불구하고 부분적인 PDF를 저장했습니다: {output_path}")
            raise
            
        finally:
            # 임시 파일 삭제
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"임시 파일 삭제 중 오류 발생: {e}")
                    # 오류가 있어도 계속 진행
    
    def _create_layout_preserved_pdf(self, original_pdf_path: str, translated_results: List[Tuple[int, str, Dict[str, Any]]], output_path: str):
        """
        원본 PDF의 레이아웃을 최대한 유지하면서 번역된 PDF를 생성합니다.
        
        Args:
            original_pdf_path: 원본 PDF 파일 경로
            translated_results: (페이지 번호, 번역된 텍스트, 페이지 요소) 튜플의 리스트
            output_path: 저장할 PDF 파일 경로
        """
        buffer = io.BytesIO()
        
        # 글로벌 font_registered 변수 사용
        global font_registered
        
        # 환경 변수 로드
        load_dotenv()
        current_os = os.getenv("CURRENT_OS", "").lower()
        
        # OS 자동 감지
        if not current_os:
            if os.name == 'nt':
                current_os = "windows"
            elif os.name == 'posix':
                if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
                    current_os = "macos"
                else:
                    current_os = "linux"
            else:
                current_os = "default"
        
        # OS에 맞는 폰트 설정 가져오기
        font_config = FONT_CONFIG.get(current_os, FONT_CONFIG["default"])
        font_name = font_config["name"]
        
        # PyMuPDF를 사용하여 원본 PDF 열기
        doc_original = fitz.open(original_pdf_path)
        
        # 새 PDF 생성
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 번역된 결과를 페이지 번호로 정렬
        translated_map = {page_num: (text, elements) for page_num, text, elements in translated_results}
        
        # 임시 파일 경로 저장 리스트
        temp_files = []
        
        try:
            # 각 페이지 처리
            for page_idx in range(len(doc_original)):
                page_num = page_idx + 1
                
                if page_num > 1:
                    # 새 페이지 시작
                    c.showPage()
                
                # 원본 페이지 정보 가져오기
                original_page = doc_original[page_idx]
                
                if page_num in translated_map:
                    translated_text, page_elements = translated_map[page_num]
                    
                    # 원본 페이지 분석하여 텍스트 블록 정보 추출
                    blocks = original_page.get_text("dict")["blocks"]
                    
                    # 번역된 텍스트를 적절한 위치에 배치
                    self._place_translated_text_in_layout(c, blocks, translated_text, font_name, width, height)
                    
                    # 이미지 추가
                    if "images" in page_elements and page_elements["images"]:
                        for img_info in page_elements["images"]:
                            try:
                                # 이미지 정보 추출
                                img_rect = img_info["rect"]
                                x0, y0 = img_rect["x0"], height - img_rect["y1"]  # 좌표계 변환
                                img_width, img_height = img_rect["width"], img_rect["height"]
                                
                                # 이미지 임시 파일로 저장
                                img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{img_info["extension"]}')
                                img_temp.write(img_info["bytes"])
                                img_temp.close()
                                temp_files.append(img_temp.name)
                                
                                # 이미지 추가
                                c.drawImage(img_temp.name, x0, y0, width=img_width, height=img_height)
                            except Exception as e:
                                print(f"이미지 추가 중 오류 발생: {e}")
                                continue
            
            # PDF 저장
            c.save()
            
            # 파일로 저장
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
                
        except Exception as e:
            print(f"레이아웃 보존 PDF 생성 중 오류 발생: {e}")
            print(f"폰트 설정: {font_name} (등록 성공: {font_registered})")
            # 오류 발생해도 buffer에 부분적으로 쓰여진 내용이 있을 수 있음
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            print(f"오류에도 불구하고 부분적인 PDF를 저장했습니다: {output_path}")
            raise
            
        finally:
            # 임시 파일 삭제
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"임시 파일 삭제 중 오류 발생: {e}")
            
            # 원본 PDF 닫기
            doc_original.close()
    
    def _place_translated_text_in_layout(self, canvas_obj, blocks, translated_text, font_name, page_width, page_height):
        """
        원본 블록 레이아웃에 맞게 번역된 텍스트를 배치합니다.
        
        Args:
            canvas_obj: ReportLab 캔버스 객체
            blocks: 원본 PDF의 텍스트 블록 정보
            translated_text: 번역된 텍스트
            font_name: 사용할 폰트 이름
            page_width: 페이지 너비
            page_height: 페이지 높이
        """
        if font_registered and font_name != "Helvetica":
            canvas_obj.setFont(font_name, 10)
        else:
            canvas_obj.setFont("Helvetica", 10)
        
        # 번역된 텍스트를 단락으로 분리
        paragraphs = translated_text.split('\n\n')
        para_index = 0
        
        # 텍스트 블록만 선택
        text_blocks = [b for b in blocks if b["type"] == 0]
        
        for block_idx, block in enumerate(text_blocks):
            if para_index >= len(paragraphs):
                break
                
            # 블록 내 라인 가져오기
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                # 각 라인의 첫 번째 스팬의 위치 정보 사용
                if "spans" not in line or not line["spans"]:
                    continue
                    
                span = line["spans"][0]
                
                # 좌표 변환 (PyMuPDF는 좌하단이 원점, ReportLab은 좌상단이 원점)
                try:
                    x0 = span["origin"][0]
                    y0 = page_height - span["origin"][1]  # y 좌표 변환
                    
                    # 폰트 크기와 색상 정보 추출
                    font_size = span.get("size", 10)
                    if font_size < 6:  # 너무 작은 폰트는 읽기 어려울 수 있으므로 최소 크기 설정
                        font_size = 6
                    
                    # 폰트 크기 설정
                    if font_registered and font_name != "Helvetica":
                        canvas_obj.setFont(font_name, font_size)
                    else:
                        canvas_obj.setFont("Helvetica", font_size)
                    
                    # 텍스트 색상 설정 (안전하게 처리)
                    try:
                        if "color" in span and isinstance(span["color"], (list, tuple)) and len(span["color"]) >= 3:
                            r, g, b = span["color"][0] / 255, span["color"][1] / 255, span["color"][2] / 255
                            canvas_obj.setFillColorRGB(r, g, b)
                        else:
                            canvas_obj.setFillColorRGB(0, 0, 0)  # 기본 검정색
                    except (TypeError, IndexError, ValueError):
                        canvas_obj.setFillColorRGB(0, 0, 0)  # 오류 시 기본 검정색
                    
                    # 현재 단락 가져오기
                    if para_index < len(paragraphs):
                        current_para = paragraphs[para_index]
                        
                        # 가용 너비에 맞게 텍스트 자르기
                        available_width = page_width - x0 - 20  # 여백 고려
                        max_chars = max(10, int(available_width / (font_size * 0.6)))  # 최소 10자
                        
                        # 다음 줄로 넘어갈 텍스트가 있는 경우
                        if len(current_para) > max_chars:
                            display_text = current_para[:max_chars]
                            paragraphs[para_index] = current_para[max_chars:]
                        else:
                            display_text = current_para
                            para_index += 1
                        
                        # 텍스트 그리기
                        canvas_obj.drawString(x0, y0, display_text)
                except (KeyError, IndexError, TypeError) as e:
                    # 오류 발생 시 다음 라인으로 진행
                    print(f"텍스트 배치 중 오류 발생: {e}")
                    continue
        
        # 남은 텍스트가 있는 경우 페이지 하단에 추가
        if para_index < len(paragraphs):
            remaining_text = '\n'.join(paragraphs[para_index:])
            
            # 기본 폰트 설정으로 돌아가기
            if font_registered and font_name != "Helvetica":
                canvas_obj.setFont(font_name, 10)
            else:
                canvas_obj.setFont("Helvetica", 10)
            
            canvas_obj.setFillColorRGB(0, 0, 0)  # 검정색
            
            # 텍스트를 여러 줄로 나누어 표시
            lines = textwrap.wrap(remaining_text, width=80)
            y = page_height - 700  # 페이지 하단에 위치
            for line in lines:
                canvas_obj.drawString(50, y, line)
                y -= 15

    def _create_translated_pdf(self, translated_results: List[Tuple[int, str]], output_path: str):
        """
        번역 결과를 PDF 파일로 생성합니다. (한글 폰트 및 Paragraph 사용으로 개선)
        
        Args:
            translated_results: (페이지 번호, 번역된 텍스트) 튜플의 리스트
            output_path: 저장할 PDF 파일 경로
        """
        buffer = io.BytesIO()
        
        # 글로벌 font_registered 변수 사용
        global font_registered
        
        # 환경 변수 로드
        load_dotenv()
        current_os = os.getenv("CURRENT_OS", "").lower()
        
        # OS 자동 감지
        if not current_os:
            if os.name == 'nt':
                current_os = "windows"
            elif os.name == 'posix':
                if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
                    current_os = "macos"
                else:
                    current_os = "linux"
            else:
                current_os = "default"
        
        # OS에 맞는 폰트 설정 가져오기
        font_config = FONT_CONFIG.get(current_os, FONT_CONFIG["default"])
        font_name = font_config["name"]
        
        # PDF 문서 설정
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # 제목 스타일 설정
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading2'],
            alignment=TA_LEFT
        )
        if font_registered and font_name != "Helvetica":
            title_style.fontName = font_name
        
        # 본문 스타일 설정 (한글 폰트 적용)
        korean_style = ParagraphStyle(
            name='KoreanStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14  # 줄 간격 설정
        )
        if font_registered and font_name != "Helvetica":
            korean_style.fontName = font_name
        
        # 전체 스토리 초기화
        story = []
        
        try:
            # 각 페이지 처리
            for page_num, text in sorted(translated_results):
                # 페이지 구분 추가
                if page_num > 1:
                    story.append(PageBreak())
                
                # 페이지 번호 추가
                page_header = Paragraph(f"=== 페이지 {page_num} ===", title_style)
                story.append(page_header)
                
                # 텍스트를 Paragraph 객체로 변환 (자동 줄바꿈 처리)
                paragraph_text = text.replace('\n', '<br/>')
                p = Paragraph(paragraph_text, korean_style)
                story.append(p)
                
                # 페이지 구분을 위한 간격 추가
                story.append(Spacer(1, 20))
            
            # PDF 빌드
            doc.build(story)
            
            # 파일로 저장
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
                
            print(f"번역된 PDF가 저장되었습니다: {output_path}")
            
        except Exception as e:
            print(f"PDF 빌드 중 오류 발생: {e}")
            print(f"폰트 설정: {font_name} (등록 성공: {font_registered})")
            # 오류 발생해도 buffer에 부분적으로 쓰여진 내용이 있을 수 있음
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            print(f"오류에도 불구하고 부분적인 PDF를 저장했습니다: {output_path}")
            raise 