"""
Gemini 클라이언트 테스트 모듈
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pdf_translator.gemini_client import GeminiClient
import google.generativeai as genai

class TestGeminiClient(unittest.TestCase):
    """
    GeminiClient 클래스를 테스트하는 테스트 케이스
    """
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # genai 모듈의 목 설정
        self.mock_genai_configure = patch('google.generativeai.configure').start()
        self.mock_generative_model = patch('google.generativeai.GenerativeModel').start()
        self.mock_list_models = patch('google.generativeai.list_models').start()
        
        # 모델 목 객체 생성
        self.mock_text_model = MagicMock()
        self.mock_vision_model = MagicMock()
        self.mock_generative_model.side_effect = [self.mock_text_model, self.mock_vision_model]
        
        # 환경 변수 목 설정
        os.environ['GEMINI_API_KEY'] = 'mock_api_key'
        
        # 테스트할 클라이언트 인스턴스 생성
        self.client = GeminiClient()
    
    def tearDown(self):
        """각 테스트 후에 실행되는 정리"""
        patch.stopall()
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
    
    def test_init_with_api_key(self):
        """API 키를 제공하여 클라이언트 초기화하는 테스트"""
        client = GeminiClient(api_key="test_key")
        
        self.assertEqual(client.api_key, "test_key")
        self.mock_genai_configure.assert_called_once_with(api_key="test_key")
    
    def test_init_from_env(self):
        """환경 변수에서 API 키를 가져와 초기화하는 테스트"""
        self.assertEqual(self.client.api_key, "mock_api_key")
        self.mock_genai_configure.assert_called_once_with(api_key="mock_api_key")
    
    def test_init_with_model_name(self):
        """모델 이름을 제공하여 초기화하는 테스트"""
        client = GeminiClient(model_name="custom-model-id")
        
        self.assertEqual(client.text_model_id, "custom-model-id")
        self.mock_generative_model.assert_any_call("custom-model-id")
    
    def test_translate_text_only(self):
        """텍스트 번역 메서드 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "번역된 텍스트"
        self.mock_text_model.generate_content.return_value = mock_response
        
        # 번역 수행
        result = self.client.translate_text_only("Text to translate", "한국어")
        
        # 결과 확인
        self.assertEqual(result, "번역된 텍스트")
        
        # 메서드 호출 확인
        self.mock_text_model.generate_content.assert_called_once()
        args = self.mock_text_model.generate_content.call_args[0][0]
        self.assertIn("Text to translate", args)
        self.assertIn("한국어", args)
    
    def test_translate_with_image(self):
        """이미지 번역 메서드 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "이미지에서 번역된 텍스트"
        self.mock_vision_model.generate_content.return_value = mock_response
        
        # 이미지 데이터
        image_data = b"fake_image_data"
        
        # 번역 수행
        result = self.client.translate(image_data, "한국어")
        
        # 결과 확인
        self.assertEqual(result, "이미지에서 번역된 텍스트")
        
        # 메서드 호출 확인
        self.mock_vision_model.generate_content.assert_called_once()
        args = self.mock_vision_model.generate_content.call_args[0][0]
        self.assertEqual(len(args), 2)
        self.assertIn("한국어", args[0])
        self.assertEqual(args[1]["mime_type"], "image/png")
        self.assertEqual(args[1]["data"], image_data)
    
    def test_translate_with_text(self):
        """텍스트로 translate 메서드 호출 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "번역된 텍스트"
        self.mock_text_model.generate_content.return_value = mock_response
        
        # 번역 수행
        result = self.client.translate("Text to translate", "한국어", text_only=True)
        
        # 결과 확인
        self.assertEqual(result, "번역된 텍스트")
        
        # 메서드 호출 확인
        self.mock_text_model.generate_content.assert_called_once()
    
    def test_translate_with_file_object(self):
        """파일 객체로 translate 메서드 호출 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "이미지에서 번역된 텍스트"
        self.mock_vision_model.generate_content.return_value = mock_response
        
        # 파일 목 생성
        mock_file = MagicMock()
        mock_file.read.return_value = b"fake_image_data"
        
        # 번역 수행
        result = self.client.translate(mock_file, "한국어")
        
        # 결과 확인
        self.assertEqual(result, "이미지에서 번역된 텍스트")
        
        # read 메서드 호출 확인
        mock_file.read.assert_called_once()
        
        # generate_content 메서드 호출 확인
        self.mock_vision_model.generate_content.assert_called_once()
    
    def test_translate_invalid_content(self):
        """유효하지 않은 콘텐츠로 translate 메서드 호출 테스트"""
        with self.assertRaises(ValueError):
            self.client.translate(123, "한국어")  # 숫자는 유효한 콘텐츠 형식이 아님
    
    def test_get_model_info(self):
        """모델 정보 가져오기 테스트"""
        # 목 모델 설정
        mock_model1 = MagicMock()
        mock_model1.name = "model1"
        mock_model1.supported_generation_methods = ["method1", "method2"]
        
        mock_model2 = MagicMock()
        mock_model2.name = "model2"
        mock_model2.supported_generation_methods = ["method3"]
        
        self.mock_list_models.return_value = [mock_model1, mock_model2]
        
        # 모델 정보 가져오기
        result = self.client.get_model_info()
        
        # 결과 확인
        self.assertEqual(result, {
            "model1": ["method1", "method2"],
            "model2": ["method3"]
        })
        
        # 메서드 호출 확인
        self.mock_list_models.assert_called_once()
    
    def test_translate_text_to_markdown(self):
        """텍스트를 마크다운으로 번역하는 메서드 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다."
        self.mock_text_model.generate_content.return_value = mock_response
        
        # 번역 수행
        result = self.client.translate_text_to_markdown("Text to translate", "한국어", 1)
        
        # 결과 확인
        self.assertEqual(result, "# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다.")
        
        # 메서드 호출 확인
        self.mock_text_model.generate_content.assert_called_once()
        args = self.mock_text_model.generate_content.call_args[0][0]
        self.assertIn("Text to translate", args)
        self.assertIn("한국어", args)
        self.assertIn("마크다운", args)
    
    def test_translate_to_markdown_with_image(self):
        """이미지를 마크다운으로 번역하는 메서드 테스트"""
        # response 목 설정
        mock_response = MagicMock()
        mock_response.text = "# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다.\n\n![이미지](IMAGE_1)"
        self.mock_vision_model.generate_content.return_value = mock_response
        
        # 이미지 데이터
        image_data = b"fake_image_data"
        
        # OS에 맞는 경로 구분자 사용
        image_path = os.path.join("images", "test_image.png")
        
        # 번역 수행
        result = self.client.translate_to_markdown(
            image_data, 
            target_language="한국어", 
            page_num=1,
            image_tag=image_path
        )
        
        # 결과 확인 - 정규화된 경로로 비교
        expected = f"# 번역된 마크다운\n\n이것은 **테스트** 마크다운입니다.\n\n![이미지]({image_path})"
        self.assertEqual(result, expected)
        
        # 메서드 호출 확인
        self.mock_vision_model.generate_content.assert_called_once()
        args = self.mock_vision_model.generate_content.call_args[0][0]
        self.assertEqual(len(args), 2)
        self.assertIn("한국어", args[0])
        self.assertIn("마크다운", args[0])
        self.assertEqual(args[1]["mime_type"], "image/png")
        self.assertEqual(args[1]["data"], image_data)
    
    def test_translate_to_markdown_with_text(self):
        """텍스트로 translate_to_markdown 메서드 호출 테스트"""
        # translate_text_to_markdown 메서드의 목 설정
        with patch.object(self.client, 'translate_text_to_markdown') as mock_method:
            mock_method.return_value = "# 번역된 마크다운\n\n텍스트 샘플"
            
            # 번역 수행
            result = self.client.translate_to_markdown("Text to translate", "한국어", 1)
            
            # 결과 확인
            self.assertEqual(result, "# 번역된 마크다운\n\n텍스트 샘플")
            
            # 메서드 호출 확인
            mock_method.assert_called_once_with("Text to translate", "한국어", 1)

if __name__ == "__main__":
    unittest.main() 