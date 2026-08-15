# 기획서: 로또 번호 생성기 무료 배포 (Render + GitHub Actions)

## 1. 배경 및 목적

현재 `lotto` 프로젝트는 로컬 환경(개인 PC)에서만 `scripts/run_web.py`로 실행 가능한 상태다. 이를 인터넷 어디서나 접속 가능한 웹사이트로 만들되, 비용은 0원으로 유지하는 것이 목표다.

검토 결과, Vercel 등 서버리스 플랫폼은 이 프로젝트의 두 가지 특성(① 로컬 SQLite 파일을 읽는 구조, ② 매주 새 회차를 수집하는 장시간 스크래핑 작업)과 구조적으로 맞지 않아 제외했다. **Render(무료 웹서비스) + GitHub Actions(무료 스케줄 작업)** 조합이 코드 변경을 최소화하면서 완전 무료로 운영 가능한 방법으로 결정됐다.

## 2. 전체 아키텍처

```
[GitHub 저장소 (lotto 프로젝트)]
        |
        |  (1) 매주 토요일 밤, GitHub Actions가 자동 실행
        v
[GitHub Actions 러너]
   - scripts/collect_draws.py 실행 (신규 회차 수집 + 통계 재계산)
   - data/lotto.db 변경사항을 저장소에 자동 커밋 & push
        |
        |  (2) main 브랜치에 push 발생 감지
        v
[Render 무료 웹서비스]
   - 자동으로 최신 코드 + 최신 lotto.db로 재배포
   - uvicorn으로 FastAPI 앱 상시 서빙 (유휴 15분 후 슬립, 요청 시 재기동)
        |
        |  (3) HTTPS로 응답
        v
[일반 사용자 브라우저]  ← xxx.onrender.com 주소로 누구나 접속
```

핵심 설계 원칙: **DB를 "서버가 직접 쓰는 대상"이 아니라 "저장소에 커밋되는 정적 자산"으로 취급**한다. Render 무료 플랜은 디스크가 재배포 시 초기화되므로, 서버가 스스로 DB를 갱신하게 만들지 않고, 대신 GitHub Actions가 갱신한 DB를 매번 새로 배포받는 방식으로 우회한다.

## 3. 구성요소별 설계

### 3-1. GitHub 저장소

- `lotto` 폴더 자체를 저장소 루트로 사용 (`lotto/lotto`, `lotto/scripts`, `lotto/data` 등 현재 구조 그대로)
- 공개 범위: **Public 권장**
  - Public이면 GitHub Actions가 시간 제한 없이 완전 무료
  - 로또 당첨번호는 공공 데이터라 코드/DB가 공개돼도 문제 없음
  - 단, 앞으로 API 키·비밀번호 등 민감정보를 코드에 넣게 되면 반드시 `.gitignore` 또는 GitHub Secrets로 분리해야 함 (Public 저장소는 커밋 즉시 전 세계에 공개됨)
- `.gitignore`에 `__pycache__/`, `server.log` 등 불필요한 파일 제외 권장

### 3-2. GitHub Actions 워크플로우

- 파일 위치: `.github/workflows/update_draws.yml`
- 트리거: 매주 토요일 로또 추첨(오후 8시 45분경) 이후 여유를 두고 실행 — 매주 토요일 21:30(KST) = UTC 12:30 기준 cron 설정
- 동작 순서:
  1. 저장소 체크아웃
  2. Python 환경 설정 + `pip install -r requirements.txt`
  3. `python scripts/collect_draws.py` 실행 (신규 회차 수집 + `number_stats` 재계산)
  4. `data/lotto.db`에 변경사항이 있으면 자동으로 git commit + push (변경 없으면 커밋 생략)
- 참고 워크플로우 예시 (실제 적용 시 세부 조정 필요):

```yaml
name: Update Lotto Draws

on:
  schedule:
    - cron: "30 12 * * 6"   # 매주 토요일 21:30 KST
  workflow_dispatch: {}      # 필요 시 수동 실행 버튼도 제공

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python scripts/collect_draws.py
      - name: Commit updated DB if changed
        run: |
          git config user.name "lotto-bot"
          git config user.email "lotto-bot@users.noreply.github.com"
          git add data/lotto.db
          git diff --cached --quiet || git commit -m "chore: update draws data"
          git push
```

### 3-3. Render 웹서비스 설정

- 서비스 타입: Web Service (무료 플랜)
- Root Directory: `lotto` (저장소 루트를 lotto 폴더로 잡았다면 비워도 됨)
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn lotto.web:app --host 0.0.0.0 --port $PORT`
  - 기존 `scripts/run_web.py`의 `reload=True`는 개발용이라 배포 시엔 사용하지 않음
  - Render가 `$PORT` 환경변수로 포트를 지정하므로 반드시 반영
- Auto-Deploy: On (main 브랜치 push 시 자동 재배포 — GitHub Actions가 push하면 자동으로 이어짐)
- 카드 등록 불필요, 매달 750 무료 인스턴스 시간 (상시 가동해도 한도 내)

### 3-4. 코드 변경사항 요약

| 파일 | 변경 내용 |
|---|---|
| `.github/workflows/update_draws.yml` | 신규 생성 |
| `.gitignore` | 신규 생성 (`__pycache__/`, `*.pyc`, `server.log` 등 제외) |
| `render.yaml` (선택) | Render 설정을 코드로 관리하고 싶다면 blueprint 파일 추가 가능 |
| 기존 `lotto/`, `scripts/` 코드 | 변경 없음 |

## 4. 공개 범위 및 접근성

- **웹사이트**: Render가 발급하는 `xxx.onrender.com` 주소로 인터넷의 누구나 접속 가능 (기본적으로 로그인/접근 제한 없음)
- **소스코드 + DB**: Public 저장소로 하면 GitHub에서도 누구나 열람 가능
- 접근을 제한하고 싶어지면 이후 별도 기능(간단한 비밀번호 등)으로 추가 가능 — 이번 배포 범위에는 포함하지 않음

## 5. 운영 중 유의사항

- Render 무료 플랜은 15분 미사용 시 슬립 → 이후 첫 방문자는 약 1분 정도 로딩 지연 경험 (허용 가능한 수준으로 판단)
- GitHub Actions 실행이 실패하는 경우(예: dhlottery.co.kr 구조 변경으로 스크래핑 실패)를 대비해, 워크플로우 실행 결과를 GitHub 저장소의 Actions 탭에서 주기적으로 확인 필요
- `data/lotto.db`가 저장소에 커밋되는 구조이므로, 저장소 용량이 서서히 증가함 (현재 80KB 수준이라 장기간 문제 없음)

## 6. 단계별 실행 순서 (사용자 작업 vs 준비 가능한 작업)

1. GitHub 계정 생성 (사용자가 이미 보유 시 생략)
2. GitHub에 `lotto` 저장소 생성 (Public) — *사용자 작업*
3. 로컬 `lotto` 폴더를 해당 저장소로 push — *사용자 작업 (또는 안내에 따라 함께 진행 가능)*
4. `.github/workflows/update_draws.yml`, `.gitignore` 파일 작성 — *준비 가능*
5. Render 계정 생성 및 GitHub 저장소 연결, Start Command 설정 — *사용자 작업 (계정 인증 필요)*
6. 최초 배포 확인 후 GitHub Actions 수동 실행(workflow_dispatch)으로 정상 동작 테스트 — *함께 진행*

## 7. 오픈 퀘스천

1. GitHub 저장소를 Public으로 진행해도 괜찮은지 (권장), 아니면 Private을 원하는지
2. GitHub 계정이 이미 있는지, 새로 만들어야 하는지
3. 워크플로우 파일(`update_draws.yml`), `.gitignore` 등을 지금 바로 lotto 폴더에 만들어 넣을지
