"""
PDF 프로세서 테스트 모듈
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pdf_translator.pdf_processor import PDFProcessor
from pdf_translator.gemini_client import GeminiClient
import tempfile

class TestPDFProcessor(unittest.TestCase):
    """
    PDFProcessor 클래스를 테스트하는 테스트 케이스
    """
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # GeminiClient 목 객체 생성
        self.mock_gemini_client = MagicMock(spec=GeminiClient)
        self.pdf_processor = PDFProcessor(gemini_client=self.mock_gemini_client)
    
    def test_init_with_client(self):
        """클라이언트를 제공하여 PDFProcessor를 초기화하는 테스트"""
        self.assertEqual(self.pdf_processor.gemini_client, self.mock_gemini_client)
    
    def test_init_without_client(self):
        """클라이언트 없이 PDFProcessor를 초기화하는 테스트"""
        # 직접 확인 대신, 생성자가 오류 없이 호출되는지 테스트
        processor = None
        try:
            processor = PDFProcessor()
            self.assertIsNotNone(processor)
            self.assertIsNotNone(processor.gemini_client)
        except Exception as e:
            self.fail(f"PDFProcessor 초기화 중 예외 발생: {e}")
    
    @patch('os.path.exists')
    def test_extract_text_file_not_found(self, mock_exists):
        """존재하지 않는 파일에 대한 예외 처리 테스트"""
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError):
            self.pdf_processor.extract_text_from_pdf("not_existing.pdf")
    
    @patch('os.path.exists')
    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader_class, mock_exists):
        """PDF에서 텍스트 추출 테스트"""
        mock_exists.return_value = True
        
        # 목 페이지 설정
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "페이지 1 텍스트"
        
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "페이지 2 텍스트"
        
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = ""  # 빈 텍스트
        
        # PDF 리더 목 설정
        mock_pdf_reader = MagicMock()
        mock_pdf_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader_class.return_value = mock_pdf_reader
        
        # open 함수 목
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.pdf_processor.extract_text_from_pdf("test.pdf")
            
            # 결과 확인
            self.assertEqual(len(result), 2)  # 비어 있지 않은 페이지만 포함
            self.assertEqual(result[0], (1, "페이지 1 텍스트"))
            self.assertEqual(result[1], (2, "페이지 2 텍스트"))
            
            # 파일 열기 확인
            mock_file.assert_called_once_with("test.pdf", 'rb')
    
    @patch('os.path.exists')
    @patch('fitz.open')
    def test_extract_page_images(self, mock_fitz_open, mock_exists):
        """PDF에서 이미지 추출 테스트"""
        mock_exists.return_value = True
        
        # 페이지 목 객체
        mock_page1 = MagicMock()
        mock_pixmap1 = MagicMock()
        mock_pixmap1.tobytes.return_value = b"page1_image_data"
        mock_page1.get_pixmap.return_value = mock_pixmap1
        
        mock_page2 = MagicMock()
        mock_pixmap2 = MagicMock()
        mock_pixmap2.tobytes.return_value = b"page2_image_data"
        mock_page2.get_pixmap.return_value = mock_pixmap2
        
        # fitz.open 목 객체
        mock_pdf_document = MagicMock()
        mock_pdf_document.__iter__.return_value = [mock_page1, mock_page2]
        mock_fitz_open.return_value = mock_pdf_document
        
        result = self.pdf_processor.extract_page_images("test.pdf")
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1, b"page1_image_data"))
        self.assertEqual(result[1], (2, b"page2_image_data"))
        
        # fitz.open 호출 확인
        mock_fitz_open.assert_called_once_with("test.pdf")
        mock_pdf_document.close.assert_called_once()
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_text_from_pdf')
    def test_translate_text_only(self, mock_extract):
        """텍스트 기반 PDF 번역 테스트"""
        # 추출된 텍스트 목 설정
        mock_extract.return_value = [
            (1, "Page 1 text"),
            (2, "Page 2 text")
        ]
        
        # GeminiClient의 번역 메서드 목 설정
        self.mock_gemini_client.translate_text_only.side_effect = ["페이지 1 텍스트", "페이지 2 텍스트"]
        
        # 번역 수행
        result = self.pdf_processor.translate_text_only("test.pdf", output_path=None)
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1, "Page 1 text", "페이지 1 텍스트"))
        self.assertEqual(result[1], (2, "Page 2 text", "페이지 2 텍스트"))
        
        # translate_text_only 메서드 호출 확인
        self.assertEqual(self.mock_gemini_client.translate_text_only.call_count, 2)
        self.mock_gemini_client.translate_text_only.assert_any_call("Page 1 text", "한국어")
        self.mock_gemini_client.translate_text_only.assert_any_call("Page 2 text", "한국어")
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.translate_text_only')
    def test_translate_with_text_only_param(self, mock_translate_text_only):
        """text_only 매개변수를 사용한 번역 테스트"""
        # translate_text_only 목 설정
        mock_translate_text_only.return_value = [
            (1, "Page 1 text", "페이지 1 텍스트"),
            (2, "Page 2 text", "페이지 2 텍스트")
        ]
        
        # 번역 수행 (text_only=True)
        result = self.pdf_processor.translate("test.pdf", text_only=True)
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1, "페이지 1 텍스트"))
        self.assertEqual(result[1], (2, "페이지 2 텍스트"))
        
        # translate_text_only 메서드 호출 확인
        mock_translate_text_only.assert_called_once_with("test.pdf", None, "한국어")
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_page_images')
    @patch('pdf_translator.pdf_processor.PDFProcessor._create_translated_pdf')
    def test_translate_multimodal(self, mock_create_pdf, mock_extract_images):
        """멀티모달 PDF 번역 테스트"""
        # 추출된 이미지 목 설정
        mock_extract_images.return_value = [
            (1, b"page1_image_data"),
            (2, b"page2_image_data")
        ]
        
        # GeminiClient의 번역 메서드 목 설정
        self.mock_gemini_client.translate.side_effect = ["페이지 1 번역", "페이지 2 번역"]
        
        # 번역 수행
        result = self.pdf_processor.translate("test.pdf", output_path="output.pdf")
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1, "페이지 1 번역"))
        self.assertEqual(result[1], (2, "페이지 2 번역"))
        
        # translate 메서드 호출 확인
        self.assertEqual(self.mock_gemini_client.translate.call_count, 2)
        self.mock_gemini_client.translate.assert_any_call(b"page1_image_data", "한국어")
        self.mock_gemini_client.translate.assert_any_call(b"page2_image_data", "한국어")
        
        # PDF 생성 메서드 호출 확인
        mock_create_pdf.assert_called_once_with(
            [(1, "페이지 1 번역"), (2, "페이지 2 번역")], 
            "output.pdf"
        )
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_text_from_pdf')
    def test_translate_text_only_with_output(self, mock_extract):
        """출력 파일이 있는 텍스트 기반 PDF 번역 테스트"""
        # 추출된 텍스트 목 설정
        mock_extract.return_value = [
            (1, "Page 1 text"),
            (2, "Page 2 text")
        ]
        
        # GeminiClient의 번역 메서드 목 설정
        self.mock_gemini_client.translate_text_only.side_effect = ["페이지 1 텍스트", "페이지 2 텍스트"]
        
        # 파일 쓰기 테스트 패치
        mock_open_file = mock_open()
        with patch('builtins.open', mock_open_file):
            # 번역 수행
            result = self.pdf_processor.translate_text_only("test.pdf", output_path="output.txt")
            
            # 결과 확인
            self.assertEqual(len(result), 2)
            
            # 파일 열기 확인
            mock_open_file.assert_called_once_with("output.txt", 'w', encoding='utf-8')
    
    @patch('io.BytesIO')
    @patch('reportlab.pdfgen.canvas.Canvas')
    def test_create_translated_pdf(self, mock_canvas_class, mock_bytesio_class):
        """번역된 PDF 생성 테스트"""
        # 목 객체 설정
        mock_buffer = MagicMock()
        mock_bytesio_class.return_value = mock_buffer
        
        mock_canvas = MagicMock()
        mock_text_object = MagicMock()
        mock_canvas.beginText.return_value = mock_text_object
        mock_canvas_class.return_value = mock_canvas
        
        # 테스트 데이터
        translated_results = [
            (1, "페이지 1 번역 텍스트"),
            (2, "페이지 2 번역 텍스트\n여러 줄 테스트")
        ]
        
        # 파일 쓰기 테스트 패치
        mock_open_file = mock_open()
        with patch('builtins.open', mock_open_file):
            # PDF 생성 메서드 호출
            self.pdf_processor._create_translated_pdf(translated_results, "output.pdf")
            
            # Canvas 생성 확인
            mock_canvas_class.assert_called_once()
            
            # showPage 호출 확인 (페이지 수만큼)
            self.assertEqual(mock_canvas.showPage.call_count, 2)
            
            # save 호출 확인
            mock_canvas.save.assert_called_once()
            
            # 파일 열기 확인
            mock_open_file.assert_called_once_with("output.pdf", 'wb')
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_page_elements')
    def test_translate_to_markdown(self, mock_extract_elements):
        """마크다운 번역 메서드 테스트"""
        # 추출된 페이지 요소 목 설정
        mock_page1 = {
            "page_num": 1,
            "width": 595,
            "height": 842,
            "text": "Page 1 text",
            "page_image": b"page1_image_data",
            "images": [
                {
                    "index": 0,
                    "xref": 123,
                    "bytes": b"image1_data",
                    "rect": {"width": 100, "height": 100, "x0": 10, "y0": 10, "x1": 110, "y1": 110},
                    "extension": "png"
                }
            ]
        }
        
        mock_extract_elements.return_value = [mock_page1]
        
        # GeminiClient의 translate_to_markdown 메서드 목 설정
        self.mock_gemini_client.translate_to_markdown.return_value = "# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다.\n\n![이미지](test_translated_images/test_translated_page_1.png)"
        
        # 임시 디렉토리에서 테스트 실행
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_translated.md")
            
            # 번역 수행
            result = self.pdf_processor.translate_to_markdown(
                pdf_path="test.pdf",
                output_path=output_path,
                target_language="한국어"
            )
            
            # 결과 확인
            self.assertIn("# 페이지 1", result)
            self.assertIn("번역된 마크다운", result)
            self.assertIn("이것은 **테스트** 마크다운입니다", result)
            
            # 파일 생성 확인
            self.assertTrue(os.path.exists(output_path))
            
            # 이미지 디렉토리 생성 확인
            images_dir = os.path.join(temp_dir, "test_translated_images")
            self.assertTrue(os.path.exists(images_dir))
            
            # GeminiClient의 translate_to_markdown 호출 확인
            self.mock_gemini_client.translate_to_markdown.assert_called_once()
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_page_elements')
    def test_translate_to_markdown_without_images(self, mock_extract_elements):
        """이미지 저장 없이 마크다운 번역 메서드 테스트"""
        # 추출된 페이지 요소 목 설정
        mock_page1 = {
            "page_num": 1,
            "width": 595,
            "height": 842,
            "text": "Page 1 text",
            "page_image": b"page1_image_data",
            "images": []
        }
        
        mock_extract_elements.return_value = [mock_page1]
        
        # GeminiClient의 translate_to_markdown 메서드 목 설정
        self.mock_gemini_client.translate_to_markdown.return_value = "# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다."
        
        # 임시 디렉토리에서 테스트 실행
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_translated.md")
            
            # 번역 수행 (save_images=False)
            result = self.pdf_processor.translate_to_markdown(
                pdf_path="test.pdf",
                output_path=output_path,
                target_language="한국어",
                save_images=False
            )
            
            # 결과 확인
            self.assertIn("# 페이지 1", result)
            self.assertIn("번역된 마크다운", result)
            
            # 파일 생성 확인
            self.assertTrue(os.path.exists(output_path))
            
            # 이미지 디렉토리가 생성되지 않았는지 확인
            images_dir = os.path.join(temp_dir, "test_translated_images")
            self.assertFalse(os.path.exists(images_dir))
            
            # GeminiClient의 translate_to_markdown 호출 확인 (image_tag=None으로 호출되어야 함)
            self.mock_gemini_client.translate_to_markdown.assert_called_once_with(
                b"page1_image_data", 
                target_language="한국어", 
                page_num=1,
                image_tag=None
            )

if __name__ == "__main__":
    unittest.main() 