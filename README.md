# 로또 번호 생성기

동행복권 로또 6/45의 역대 당첨 번호를 수집하고 출현 빈도를 계산해 여러 규칙으로 번호 조합을 생성하는 FastAPI 웹 애플리케이션입니다.

> 과거 출현 빈도는 다음 회차의 당첨 확률을 높이지 않습니다. 모든 번호 조합의 당첨 확률은 동일하며, 이 프로젝트는 통계 탐색과 오락을 목적으로 합니다.

## 주요 기능

- 동행복권 회차별 당첨 번호 수집 및 SQLite 저장
- 전체 회차와 최근 100회 기준 번호별 출현 통계 계산
- 여섯 가지 규칙을 이용한 번호 조합 생성
- 생성 개수 선택, 조합 복사, 장바구니, 오늘의 번호, 다크 모드를 제공하는 웹 UI
- 번호 생성 및 데이터 검증용 CLI 스크립트

## 번호 생성 규칙

| 규칙 | 설명 |
| --- | --- |
| `independent` | 고빈도 3개와 저빈도 1개를 고정하고, 나머지 2개를 고·저빈도 그룹에서 각각 독립적으로 선택합니다. |
| `fixed` | 고빈도 4개와 저빈도 2개를 선택합니다. |
| `all_high` | 전체 통계의 고빈도 상위 15개 번호에서 6개를 선택합니다. |
| `all_low` | 전체 통계의 저빈도 하위 15개 번호에서 6개를 선택합니다. |
| `biased` | 최근 100회 통계를 기준으로 `independent` 규칙을 적용합니다. |
| `unpopular` | 생일 범위, 연속수, 등차수열 등 사람들이 흔히 고를 법한 패턴을 피한 조합을 탐색합니다. |

## 기술 스택

- Python 3.10+
- FastAPI / Uvicorn
- Requests
- SQLite

## 시작하기

### 1. 가상 환경과 의존성 설치

Windows PowerShell 기준입니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

macOS 또는 Linux에서는 다음과 같이 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 2. 데이터 수집

저장소에는 초기 데이터베이스가 포함되어 있습니다. 최신 회차를 반영하거나 DB를 새로 구성하려면 다음 명령을 실행합니다.

```powershell
py scripts/collect_draws.py
```

수집 결과와 통계 정합성은 다음 명령으로 확인할 수 있습니다.

```powershell
py scripts/check_db.py
```

### 3. 웹 서버 실행

```powershell
py scripts/run_web.py
```

브라우저에서 <http://127.0.0.1:8000>으로 접속합니다. 개발용 실행 스크립트는 코드 변경 시 자동으로 서버를 다시 시작합니다.

운영 환경에서는 다음 명령을 권장합니다.

```bash
uvicorn lotto.web:app --host 0.0.0.0 --port 8000
```

## CLI 사용법

대표 생성 규칙의 번호를 터미널에서 바로 확인할 수 있습니다.

```powershell
py scripts/generate_numbers.py
```

## API

### `GET /api/generate`

지정한 규칙으로 번호 조합을 생성합니다.

| 매개변수 | 기본값 | 설명 |
| --- | --- | --- |
| `rule` | `independent` | 번호 생성 규칙 |
| `count` | `5` | 생성할 조합 수(1~20) |

예시:

```text
GET /api/generate?rule=biased&count=5
```

### `GET /api/weekly`

여섯 가지 규칙에서 각각 한 조합씩 생성합니다.

FastAPI가 제공하는 대화형 API 문서는 서버 실행 후 <http://127.0.0.1:8000/docs>에서 확인할 수 있습니다.

## 프로젝트 구조

```text
.
├── data/
│   └── lotto.db              # 당첨 번호와 통계 SQLite DB
├── docs/                     # 설계 및 배포 문서
├── lotto/
│   ├── collect.py            # 전체 회차 수집
│   ├── db.py                 # DB 연결 및 스키마
│   ├── fetch.py              # 동행복권 HTTP 요청
│   ├── generate.py           # 번호 생성 규칙
│   ├── stats.py              # 전체·최근 출현 통계
│   ├── templates.py          # 웹 UI 템플릿
│   └── web.py                # FastAPI 앱과 API
├── scripts/                  # 실행·수집·검증 스크립트
└── requirements.txt
```

## 데이터 갱신 흐름

1. 동행복권 결과 페이지에서 최신 회차를 확인합니다.
2. 10회차 단위 API를 역순으로 조회합니다.
3. 아직 저장되지 않은 회차만 `draws` 테이블에 추가합니다.
4. `number_stats`와 `number_stats_recent` 통계를 다시 계산합니다.

데이터 수집은 동행복권 사이트의 응답 형식과 이용 가능 여부에 영향을 받을 수 있습니다.

