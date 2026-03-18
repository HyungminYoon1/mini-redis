# Tests And Debugging

## 왜 `unittest`를 썼는가

현재 환경에는 `pytest`가 설치돼 있지 않았다.  
학습용 프로젝트에서 테스트 실행까지 외부 의존성에 묶이면 진입 장벽이 커진다.

그래서 이 저장소는 표준 라이브러리 `unittest`만으로 검증 가능하게 만들었다.

## 테스트 구성

### `tests/test_protocol.py`

RESP3 인코딩/디코딩을 검증한다.

- `HELLO 3` 요청 파싱
- map 응답 round-trip
- blob string 인코딩/디코딩

여기서 배워야 할 것은 "프로토콜 계층은 서버가 없어도 테스트할 수 있다"는 점이다.

### `tests/test_command_service.py`

명령 의미와 TTL 규칙을 검증한다.

- `SET/GET/DEL`
- `EXPIRE/TTL`
- `SET`이 기존 TTL을 지우는지

이 테스트는 `FakeClock`을 쓴다.  
시간이 개입되면 실제 시계를 쓰는 순간 테스트가 불안정해지기 때문이다.

### `tests/test_integration.py`

서버와 CLI를 실제로 붙여서 검증한다.

- CLI `SET/GET` round-trip
- `HELLO 3` 없이 명령을 보내면 거부되는지
- 없는 key 조회 시 `(nil)`이 나오는지

즉, 단위 테스트와 통합 테스트를 분리해 두었다.

## 이번 구현에서 실제로 겪은 문제

### 1. Python 3.9와 타입 표기

처음에는 `str | None` 같은 3.10 스타일 표기를 썼다.  
현재 환경은 Python 3.9라 import 단계에서 깨졌다.

해결:

- `from __future__ import annotations` 추가

학습 포인트:

- 타입 힌트도 런타임 호환성에 영향을 줄 수 있다

### 2. `cmd` 패키지 이름

테스트에서 `cmd.mini_redis_cli.main`을 직접 import하려고 하니 표준 라이브러리 `cmd`와 충돌했다.

해결:

- 통합 테스트는 CLI 파일을 경로 기반으로 로드

학습 포인트:

- 패키지 이름은 표준 라이브러리와 충돌하지 않게 잡는 편이 좋다

### 3. 샌드박스의 로컬 포트 바인딩 제한

통합 테스트는 서버가 localhost 포트에 bind해야 하는데, 현재 작업 환경의 제한 때문에 일반 실행에서 실패했다.

해결:

- 제한이 없는 권한으로 통합 테스트를 재실행해 검증

학습 포인트:

- 실패가 항상 코드 버그는 아니다
- 실행 환경의 제약도 디버깅 대상이다
