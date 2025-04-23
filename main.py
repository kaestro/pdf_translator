#!/usr/bin/env python
"""
PDF 번역기 메인 실행 파일

Gemini API를 사용하여 PDF 파일을 한국어로 번역하는 프로그램입니다.
"""

import os
import argparse
import sys
from dotenv import load_dotenv
from pdf_translator.gemini_client import GeminiClient
from pdf_translator.pdf_processor import PDFProcessor
from pdf_translator.gemini_models import GeminiModel

def main():
    """
    메인 함수
    """
    # 환경 변수 로드
    load_dotenv()
    
    # API 키 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("오류: Gemini API 키가 설정되지 않았습니다.")
        print("다음 방법 중 하나로 API 키를 설정하세요:")
        print("1. .env 파일에 GEMINI_API_KEY=your_key 추가")
        print("2. 환경 변수 GEMINI_API_KEY 설정")
        print("3. --api-key 인자 사용")
        return 1
    
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="PDF 파일을 한국어로 번역하는 도구")
    parser.add_argument("pdf_file", nargs="?", help="번역할 PDF 파일 경로")
    parser.add_argument("-o", "--output", help="번역 결과를 저장할 파일 경로")
    parser.add_argument("-l", "--language", default="한국어", help="번역할 대상 언어 (기본값: 한국어)")
    parser.add_argument("-k", "--api-key", help="Gemini API 키 (환경 변수나 .env 파일 대신 사용)")
    parser.add_argument("-m", "--model", 
                      choices=[m.name for m in GeminiModel if not m.name.startswith("_")], 
                      default="GEMINI_1_5_FLASH", 
                      help="사용할 Gemini 모델 (기본값: GEMINI_1_5_FLASH)")
    parser.add_argument("--list-models", action="store_true", help="사용 가능한 모델 목록 표시")
    parser.add_argument("--text-only", action="store_true", help="텍스트만 추출하여 번역 (멀티모달 번역 비활성화)")
    parser.add_argument("--pdf-output", action="store_true", help="번역 결과를 PDF 파일로 저장 (멀티모달 모드에서만 사용 가능)")
    
    args = parser.parse_args()
    
    # 모델 목록 표시 요청 처리
    if args.list_models:
        print("사용 가능한 Gemini 모델 목록:")
        for model in GeminiModel:
            if not model.name.startswith("_"):  # 숨겨진 모델 제외
                print(f"  {model.name}: {model.value}")
        return 0
    
    # PDF 파일이 제공되지 않은 경우 도움말 출력
    if not args.pdf_file:
        parser.print_help()
        return 1
    
    # 입력 파일 확인
    if not os.path.exists(args.pdf_file):
        print(f"오류: PDF 파일을 찾을 수 없습니다: {args.pdf_file}")
        return 1
    
    # 출력 파일 설정
    output_path = args.output
    if not output_path:
        base_name = os.path.basename(args.pdf_file)
        file_name = os.path.splitext(base_name)[0]
        # 멀티모달 모드와 PDF 출력 옵션이 사용된 경우 PDF 출력 확장자 사용
        if not args.text_only and args.pdf_output:
            output_path = f"{file_name}_translated.pdf"
        else:
            output_path = f"{file_name}_translated.txt"
    
    try:
        # 선택한 모델 확인
        model_name = args.model
        # 모델이 Enum에 있는지 확인
        if not hasattr(GeminiModel, model_name):
            print(f"오류: 유효하지 않은 모델 이름입니다: {model_name}")
            print("'--list-models' 옵션을 사용하여 사용 가능한 모델 목록을 확인하세요.")
            return 1
            
        model_id = GeminiModel[model_name].value
        print(f"선택한 모델: {model_name} ({model_id})")
        
        # Gemini 클라이언트 및 PDF 프로세서 초기화
        gemini_client = GeminiClient(api_key=args.api_key or api_key, model_name=model_id)
        pdf_processor = PDFProcessor(gemini_client=gemini_client)
        
        # PDF 번역
        if args.text_only:
            print("텍스트 추출 모드로 번역을 시작합니다...")
            pdf_processor.translate_text_only(
                pdf_path=args.pdf_file,
                output_path=output_path,
                target_language=args.language
            )
            print(f"번역이 완료되었습니다. 결과는 {output_path}에 저장되었습니다.")
        else:
            print("멀티모달 모드로 번역을 시작합니다...")
            
            # PDF 출력 옵션이 사용되지 않았고 출력 확장자가 .pdf가 아닌 경우, 확장자 변경
            if args.pdf_output and not output_path.lower().endswith('.pdf'):
                output_path = os.path.splitext(output_path)[0] + '.pdf'
                print(f"PDF 출력 옵션이 지정되어 출력 파일을 {output_path}로 변경합니다.")
            
            pdf_processor.translate(
                pdf_path=args.pdf_file,
                output_path=output_path,
                target_language=args.language,
                text_only=False
            )
            print(f"번역이 완료되었습니다. 결과는 {output_path}에 저장되었습니다.")
        
        return 0
        
    except KeyError as e:
        print(f"오류: 모델을 찾을 수 없습니다: {e}")
        print("'--list-models' 옵션을 사용하여 사용 가능한 모델 목록을 확인하세요.")
        return 1
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        print("다른 모델을 시도해보세요. '--list-models' 옵션으로 사용 가능한 모델 목록을 확인할 수 있습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
