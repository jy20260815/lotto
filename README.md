# 로또 번호 생성기

동행복권 로또 6/45의 역대 당첨 번호를 수집하고 출현 빈도를 계산해 여러 규칙으로 번호 조합을 생성하는 FastAPI 웹 애플리케이션입니다.

> 과거 출현 빈도는 다음 회차의 당첨 확률을 높이지 않습니다. 모든 번호 조합의 당첨 확률은 동일하며, 이 프로젝트는 통계 탐색과 오락을 목적으로 합니다.

## 주요 기능

- 동행복권 회차별 당첨 번호 수집 및 SQLite 저장
- 전체 회차와 최근 100회 기준 번호별 출현 통계 계산
- 여섯 가지 규칙을 이용한 번호 조합 생성
- 고정수·제외수·홀짝 비율·합계 범위 조건을 건 번호 생성
- 회차별 당첨 결과 조회와 직접 입력한 번호·장바구니 조합의 당첨 확인(1~5등)
- 번호별 출현 빈도, 홀짝·구간·합계 분포 차트 (전체/최근 100·50·20회)
- 규칙별 백테스트: 과거 각 회차 이전 데이터만으로 번호를 만들어 실제 결과와 비교
- 구매 시뮬레이션: 최근 5회차에 회차마다 5개~1,000만 개씩 샀다면 등수별로 몇 개 당첨됐을지 모의 계산
- 생성 개수 선택, 조합 복사, 장바구니, 오늘의 번호, 다크 모드를 제공하는 모바일 대응 웹 UI
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

- Python 3.12+
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
| `include` | 없음 | 반드시 포함할 번호, 쉼표 구분(최대 5개) |
| `exclude` | 없음 | 제외할 번호, 쉼표 구분 |
| `odd` | 없음 | 홀수 개수(0~6) |
| `sum_min`, `sum_max` | `21`, `255` | 번호 6개 합계 범위 |

고정수는 규칙이 뽑은 번호 중 일부를 대체하고, 조건을 만족할 수 없으면 `422`를 반환합니다.

예시:

```text
GET /api/generate?rule=biased&count=5&include=7&exclude=1,2&odd=3&sum_min=100&sum_max=170
```

### `GET /api/weekly`

여섯 가지 규칙에서 각각 한 조합씩 생성합니다.

### `GET /api/draws`, `GET /api/draws/latest`, `GET /api/draws/{round}`

최근 회차 목록(`limit`, 기본 10), 최신 회차, 특정 회차의 당첨 번호와 보너스 번호를 반환합니다.

### `POST /api/check`

조합들의 당첨 등수를 확인합니다. `round`를 생략하면 최신 회차 기준입니다.

```json
{"tickets": [[3, 11, 19, 27, 34, 42]], "round": 1241}
```

### `GET /api/stats`

번호별 출현 횟수와 미출현 기간, 홀짝·구간·합계 분포를 반환합니다. `window=0`은 전체 회차, 양수는 최근 N회차입니다.

### `GET /api/backtest`

최근 `rounds`회(10~300)의 각 회차에 대해 그 이전 데이터만으로 규칙마다 `tickets`개(1~10)씩 생성해 결과를 맞춰보고, 무작위 선택 및 이론 기댓값과 비교합니다. `seed`를 주면 결과가 재현됩니다.

### `GET /api/simulate`

최근 `rounds`회(기본 5, 최대 10) 각 회차에 자동(무작위) 번호를 5·10·50·100·1,000·1만·10만·100만·1,000만 개씩 샀다고 가정해 등수별 당첨 개수를 계산합니다. 1,000개 이하는 번호를 실제로 뽑아 맞춰보고, 그보다 많으면 같은 분포를 가지는 다항분포에서 바로 뽑습니다. `seed`를 주면 결과가 재현됩니다.

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
│   ├── generate.py           # 번호 생성 규칙과 생성 조건
│   ├── stats.py              # 전체·최근 출현 통계 (DB 테이블 갱신)
│   ├── analysis.py           # 통계 탭용 분포 요약
│   ├── check.py              # 회차 조회와 당첨 등수 계산
│   ├── backtest.py           # 규칙별 백테스트
│   ├── simulate.py           # 구매 개수별 당첨 시뮬레이션
│   ├── static/               # 웹 UI (index.html, app.css, app.js)
│   └── web.py                # FastAPI 앱과 API
├── scripts/                  # 실행·수집·검증 스크립트
├── tests/                    # unittest 테스트
└── requirements.txt
```

## 테스트

추가 패키지 없이 표준 `unittest`로 실행합니다. 저장소의 `data/lotto.db`를 읽기 전용으로 사용합니다.

```powershell
py -m unittest discover tests
```

## 데이터 갱신 흐름

1. 동행복권 결과 페이지에서 최신 회차를 확인합니다.
2. 10회차 단위 API를 역순으로 조회합니다.
3. 아직 저장되지 않은 회차만 `draws` 테이블에 추가합니다.
4. `number_stats`와 `number_stats_recent` 통계를 다시 계산합니다.

데이터 수집은 동행복권 사이트의 응답 형식과 이용 가능 여부에 영향을 받을 수 있습니다.

### 자동 갱신

- **수집**: GitHub Actions(`.github/workflows/update_draws.yml`)가 매주 토요일 23:30(KST)에 위 흐름을 실행하고 변경된 `data/lotto.db`를 커밋합니다.
- **로컬 반영**: `scripts/sync_data.py`가 `git pull --ff-only`로 최신 DB를 받아옵니다. `main` 브랜치이고 커밋되지 않은 변경이 없을 때만 동작하며, 결과는 `sync_data.log`에 남습니다.

로컬 동기화를 Windows 작업 스케줄러에 등록하면 매주 일요일 09:00에 실행되고, PC가 꺼져 있었다면 다음에 켜질 때 실행됩니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_sync_task.ps1   # 등록
Unregister-ScheduledTask -TaskName "LottoDataSync" -Confirm:$false       # 삭제
```

수집은 GitHub Actions 한 곳에서만 하므로, 로컬에서 `collect_draws.py`로 DB를 따로 갱신해 커밋하면 봇의 커밋과 바이너리 충돌이 날 수 있습니다.

