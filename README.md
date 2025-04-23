# PDF 번역기 (PDF Translator)

Gemini API를 사용하여 PDF 문서를 한국어로 번역하는 프로그램입니다.

## 기능

- PDF 파일에서 텍스트 추출
- Gemini API를 사용한 텍스트 번역
- 번역 결과를 파일로 저장
- 다양한 Gemini 모델 지원

## 설치 방법

이 프로젝트는 uv 패키지 매니저를 사용합니다.

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source .venv/bin/activate

# uv 설치
pip install uv

# 프로젝트 설치
uv pip install -e .
```

## API 키 설정

Gemini API를 사용하기 위해서는 API 키가 필요합니다. 다음 방법 중 하나로 API 키를 설정하세요:

1. `.env` 파일 생성:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. 환경 변수 설정:
   ```bash
   # Windows
   set GEMINI_API_KEY=your_gemini_api_key_here
   
   # Linux/Mac
   export GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. 명령행 인자 사용:
   ```bash
   python main.py your_pdf_file.pdf --api-key your_gemini_api_key_here
   ```

## 사용 방법

```bash
# 기본 사용법
python main.py your_pdf_file.pdf

# 출력 파일 지정
python main.py your_pdf_file.pdf -o translated_output.txt

# 번역할 언어 지정 (기본값: 한국어)
python main.py your_pdf_file.pdf -l 일본어

# 사용할 Gemini 모델 지정 (기본값: GEMINI_1_5_FLASH)
python main.py your_pdf_file.pdf -m GEMINI_1_5_PRO

# 사용 가능한 모델 목록 표시
python main.py --list-models
```

### 사용 가능한 주요 모델

- `GEMINI_1_5_FLASH`: Gemini 1.5 Flash (기본 모델)
- `GEMINI_1_5_PRO`: Gemini 1.5 Pro
- `GEMINI_1_5_PRO_LATEST`: Gemini 1.5 Pro 최신 버전
- `GEMINI_2_0_FLASH`: Gemini 2.0 Flash
- `GEMINI_1_0_PRO_VISION_LATEST`: Gemini 1.0 Pro Vision (이미지 이해 가능)

전체 모델 목록은 `--list-models` 옵션으로 확인할 수 있습니다.

> **참고**: 일부 모델은 Google API에서 제공되지 않을 수 있습니다. 404 오류가 발생한다면 다른 모델을 사용해보세요.

## 테스트 실행

```bash
# 모든 테스트 실행
python -m unittest discover

# 특정 테스트 실행
python -m unittest tests.test_gemini_client
python -m unittest tests.test_pdf_processor
```

## 프로젝트 구조

```
pdf_translator/
├── pdf_translator/
│   ├── __init__.py
│   ├── gemini_client.py
│   ├── gemini_models.py
│   └── pdf_processor.py
├── tests/
│   ├── __init__.py
│   ├── test_gemini_client.py
│   └── test_pdf_processor.py
├── .env
├── main.py
├── pyproject.toml
└── README.md
```

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.
