# PDF 번역기 (PDF Translator)

Gemini API를 사용하여 PDF 문서를 한국어로 번역하는 프로그램입니다.

## 기능

- PDF 파일에서 텍스트 추출
- 멀티모달 기능을 통한 PDF 이미지 번역 (레이아웃, 그림, 도표 등 포함)
- Gemini API를 사용한 텍스트 및 이미지 번역
- 번역 결과를 텍스트 또는 PDF 파일로 저장
- 한국어 폰트 지원 (운영체제별 자동 감지 또는 수동 설정)
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

## API 키 및 환경 설정

### API 키 설정

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

### 운영체제 설정 (한글 폰트용)

프로그램은 자동으로 운영체제를 감지하여 적절한 한글 폰트를 사용합니다. 그러나 수동으로 운영체제를 지정하려면 `.env` 파일에 다음과 같이 설정할 수 있습니다:

```
CURRENT_OS=windows  # 윈도우 (맑은 고딕 폰트 사용)
CURRENT_OS=macos    # macOS (애플고딕 폰트 사용)
CURRENT_OS=linux    # 리눅스 (나눔고딕 폰트 사용, 미리 설치 필요)
```

리눅스에서 나눔고딕 폰트를 설치하는 방법:
```bash
# Ubuntu/Debian 계열
sudo apt-get install fonts-nanum

# Fedora/CentOS 계열
sudo dnf install google-nanum-gothic-fonts
```

## 사용 방법

```bash
# 기본 사용법 (멀티모달 모드)
python main.py your_pdf_file.pdf

# 텍스트만 추출하여 번역 (기존 방식)
python main.py your_pdf_file.pdf --text-only

# 멀티모달 모드에서 PDF 출력
python main.py your_pdf_file.pdf --pdf-output

# 출력 파일 지정
python main.py your_pdf_file.pdf -o translated_output.txt

# 번역할 언어 지정 (기본값: 한국어)
python main.py your_pdf_file.pdf -l 일본어

# 사용할 Gemini 모델 지정 (기본값: GEMINI_1_5_FLASH)
python main.py your_pdf_file.pdf -m GEMINI_1_5_PRO

# 사용 가능한 모델 목록 표시
python main.py --list-models
```

### 번역 모드

- **멀티모달 모드 (기본)**: PDF 페이지의 이미지를 캡처하여 Gemini API로 전송합니다. 이 모드에서는 텍스트뿐만 아니라 이미지, 차트, 도표 등을 포함한 전체 내용을 번역할 수 있습니다.
  ```bash
  python main.py your_pdf_file.pdf
  ```

- **텍스트 전용 모드**: PDF에서 텍스트만 추출하여 번역합니다. 이미지나 복잡한 레이아웃은 무시됩니다.
  ```bash
  python main.py your_pdf_file.pdf --text-only
  ```

### 출력 형식

- **텍스트 파일 (기본)**: 번역 결과를 텍스트 파일로 저장합니다.
  ```bash
  python main.py your_pdf_file.pdf -o output.txt
  ```

- **PDF 파일 (멀티모달 모드에서만 가능)**: 번역 결과를 PDF 파일로 저장합니다. 한국어 폰트가 지원됩니다.
  ```bash
  python main.py your_pdf_file.pdf --pdf-output
  ```

### 한국어 폰트 문제 해결

PDF 출력에서 한국어가 깨지는 경우:

1. `.env` 파일에 `CURRENT_OS` 환경변수가 정확히 설정되었는지 확인하세요.
2. 콘솔 출력을 확인하여 폰트 등록 성공 여부를 확인하세요.
3. 리눅스 사용자는 나눔고딕 폰트가 설치되어 있는지 확인하세요.
4. 자신의 환경에 맞는 폰트 경로를 수동으로 설정하려면 `pdf_translator/pdf_processor.py` 파일의 `FONT_CONFIG` 딕셔너리를 수정하세요.

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
# 테스트 의존성 설치
pip install pytest

# 모든 테스트 실행
python -m pytest

# 상세 출력으로 테스트 실행
python -m pytest -v

# 특정 테스트 실행
python -m pytest tests/test_gemini_client.py
python -m pytest tests/test_pdf_processor.py
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
