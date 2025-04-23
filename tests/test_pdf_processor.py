"""
PDF 프로세서 테스트 모듈
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pdf_translator.pdf_processor import PDFProcessor
from pdf_translator.gemini_client import GeminiClient

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
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_text_from_pdf')
    def test_translate_pdf(self, mock_extract):
        """PDF 번역 테스트"""
        # 추출된 텍스트 목 설정
        mock_extract.return_value = [
            (1, "Page 1 text"),
            (2, "Page 2 text")
        ]
        
        # GeminiClient의 번역 메서드 목 설정
        self.mock_gemini_client.translate.side_effect = ["페이지 1 텍스트", "페이지 2 텍스트"]
        
        # 번역 수행
        result = self.pdf_processor.translate_pdf("test.pdf", output_path=None)
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (1, "Page 1 text", "페이지 1 텍스트"))
        self.assertEqual(result[1], (2, "Page 2 text", "페이지 2 텍스트"))
        
        # translate 메서드 호출 확인
        self.assertEqual(self.mock_gemini_client.translate.call_count, 2)
        self.mock_gemini_client.translate.assert_any_call("Page 1 text", "한국어")
        self.mock_gemini_client.translate.assert_any_call("Page 2 text", "한국어")
    
    @patch('pdf_translator.pdf_processor.PDFProcessor.extract_text_from_pdf')
    def test_translate_pdf_with_output(self, mock_extract):
        """출력 파일이 있는 PDF 번역 테스트"""
        # 추출된 텍스트 목 설정
        mock_extract.return_value = [
            (1, "Page 1 text"),
            (2, "Page 2 text")
        ]
        
        # GeminiClient의 번역 메서드 목 설정
        self.mock_gemini_client.translate.side_effect = ["페이지 1 텍스트", "페이지 2 텍스트"]
        
        # 파일 쓰기 테스트 패치
        mock_open_file = mock_open()
        with patch('builtins.open', mock_open_file):
            # 번역 수행
            result = self.pdf_processor.translate_pdf("test.pdf", output_path="output.txt")
            
            # 결과 확인
            self.assertEqual(len(result), 2)
            
            # 파일 열기 확인
            mock_open_file.assert_called_once_with("output.txt", 'w', encoding='utf-8')

if __name__ == "__main__":
    unittest.main() 