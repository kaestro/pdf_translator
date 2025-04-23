"""
Gemini 모델 목록

이 모듈은 Google Gemini API에서 사용 가능한 모델 목록을 Enum 형태로 제공합니다.
"""

from enum import Enum, auto

class GeminiModel(Enum):
    """
    Gemini API에서 사용 가능한 모델 목록입니다.
    
    사용 예:
        model_name = GeminiModel.GEMINI_1_5_PRO.value
    """
    # Gemini 1.0 모델
    GEMINI_1_0_PRO_VISION_LATEST = "models/gemini-1.0-pro-vision-latest"
    GEMINI_PRO_VISION = "models/gemini-pro-vision"
    
    # Gemini 1.5 모델
    GEMINI_1_5_PRO_LATEST = "models/gemini-1.5-pro-latest"
    GEMINI_1_5_PRO_001 = "models/gemini-1.5-pro-001"
    GEMINI_1_5_PRO_002 = "models/gemini-1.5-pro-002"
    GEMINI_1_5_PRO = "models/gemini-1.5-pro"
    GEMINI_1_5_FLASH_LATEST = "models/gemini-1.5-flash-latest"
    GEMINI_1_5_FLASH_001 = "models/gemini-1.5-flash-001"
    GEMINI_1_5_FLASH_001_TUNING = "models/gemini-1.5-flash-001-tuning"
    GEMINI_1_5_FLASH = "models/gemini-1.5-flash"
    GEMINI_1_5_FLASH_002 = "models/gemini-1.5-flash-002"
    GEMINI_1_5_FLASH_8B = "models/gemini-1.5-flash-8b"
    GEMINI_1_5_FLASH_8B_001 = "models/gemini-1.5-flash-8b-001"
    GEMINI_1_5_FLASH_8B_LATEST = "models/gemini-1.5-flash-8b-latest"
    
    # Gemini 2.0 모델
    GEMINI_2_0_FLASH = "models/gemini-2.0-flash"
    GEMINI_2_0_FLASH_001 = "models/gemini-2.0-flash-001"
    GEMINI_2_0_FLASH_LITE_001 = "models/gemini-2.0-flash-lite-001"
    GEMINI_2_0_FLASH_LITE = "models/gemini-2.0-flash-lite"
    GEMINI_2_0_FLASH_LIVE_001 = "models/gemini-2.0-flash-live-001"
    
    # Gemini 2.5 모델
    GEMINI_2_5_PRO_EXP_03_25 = "models/gemini-2.5-pro-exp-03-25"
    GEMINI_2_5_PRO_PREVIEW_03_25 = "models/gemini-2.5-pro-preview-03-25"
    GEMINI_2_5_FLASH_PREVIEW_04_17 = "models/gemini-2.5-flash-preview-04-17"
    
    # Gemma 모델
    GEMMA_3_1B_IT = "models/gemma-3-1b-it"
    GEMMA_3_4B_IT = "models/gemma-3-4b-it"
    GEMMA_3_12B_IT = "models/gemma-3-12b-it"
    GEMMA_3_27B_IT = "models/gemma-3-27b-it"
    
    # 임베딩 모델
    EMBEDDING_001 = "models/embedding-001"
    TEXT_EMBEDDING_004 = "models/text-embedding-004"
    GEMINI_EMBEDDING_EXP_03_07 = "models/gemini-embedding-exp-03-07"
    GEMINI_EMBEDDING_EXP = "models/gemini-embedding-exp"
    
    # 실험적/레거시 모델
    CHAT_BISON_001 = "models/chat-bison-001"
    TEXT_BISON_001 = "models/text-bison-001"
    EMBEDDING_GECKO_001 = "models/embedding-gecko-001"
    AQA = "models/aqa"
    IMAGEN_3_0_GENERATE_002 = "models/imagen-3.0-generate-002"
    
    @staticmethod
    def get_default_model():
        """기본 모델을 반환합니다."""
        return GeminiModel.GEMINI_1_5_FLASH.value
        
    @staticmethod
    def get_model_by_name(name):
        """모델 이름으로 모델을 검색합니다."""
        try:
            return GeminiModel[name].value
        except KeyError:
            # 일치하는 이름이 없으면 기본 모델 반환
            return GeminiModel.get_default_model() 