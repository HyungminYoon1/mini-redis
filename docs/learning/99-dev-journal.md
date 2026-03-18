# Development Journal

## Entry 1. 문서화 방식 결정

### 목표

이 프로젝트를 "코드만 남는 결과물"이 아니라, Redis를 공부할 수 있는 자료로 만들기.

### 결정

- 기존 `docs/`는 요구사항과 설계 문서로 유지
- 새 `docs/learning/`은 학습용 설명서로 운영
- 주제별 문서와 시간순 저널을 함께 남기기

### 이유

한 파일짜리 로그는 흐름은 좋지만 찾아보기 어렵다.  
주제별 문서만 두면 구현의 실제 히스토리가 사라진다.  
그래서 "주제 문서 + 저널" 구조를 택했다.

## Entry 2. RESP3 계층 구현

### 목표

서버와 CLI가 공통으로 쓸 수 있는 프로토콜 계층 만들기.

### 바꾼 파일

- `internal/protocol/resp/types.py`
- `internal/protocol/resp/request_decoder.py`
- `internal/protocol/resp/response_encoder.py`
- `internal/protocol/resp/socket_io.py`
- `internal/protocol/resp/errors.py`
- `internal/protocol/resp/hello_handler.py`

### 핵심 결정

- RESP 값을 `RespValue(kind, value)`로 통일
- decode와 socket reading을 분리
- incomplete frame과 malformed frame을 서로 다른 예외로 구분

### 배운 점

프로토콜 구현의 핵심은 "문자열 파싱"이 아니라 "자료구조와 버퍼 상태를 다루는 일"이다.

## Entry 3. 명령과 TTL 구현

### 목표

문서를 실제 동작으로 바꾸기.

### 바꾼 파일

- `internal/command/parser.py`
- `internal/command/validator.py`
- `internal/service/*.py`
- `internal/expiration/*.py`
- `internal/repository/*.py`

### 핵심 결정

- parser는 RESP Array를 `Command`로 변환만 한다
- validator는 규칙만 검사한다
- service는 실행만 담당한다
- TTL은 value 저장소와 분리된 저장소에서 관리한다

### 배운 점

Redis를 이해하려면 "명령 하나가 어느 상태를 읽고 어느 상태를 바꾸는지"를 추적해야 한다.  
`SET`이 왜 TTL을 지우는지 이해하면, key-value 저장 이상의 상태 모델이 보이기 시작한다.

## Entry 4. 서버와 CLI 연결

### 목표

문서 속 설계를 실제 네트워크 프로그램으로 완성하기.

### 바꾼 파일

- `internal/server/server.py`
- `internal/server/session_handler.py`
- `internal/server/shutdown.py`
- `cmd/mini_redis_server/main.py`
- `cmd/mini_redis_cli/main.py`

### 핵심 결정

- 세션 시작 전 `HELLO 3` 강제
- 연결은 여러 개 받을 수 있지만 명령 실행은 lock으로 단순화
- CLI가 handshake와 일반 명령을 모두 담당

### 배운 점

서버 구현은 명령 로직만 짜는 일이 아니다.  
소켓, 버퍼, 프로토콜, 상태, 오류, 출력 형식을 한 흐름으로 이어 붙이는 작업이다.

## Entry 5. 테스트와 환경 이슈

### 목표

이 구현이 "돌아가는 것처럼 보이는 코드"가 아니라, 실제로 검증된 코드가 되게 만들기.

### 바꾼 파일

- `tests/test_protocol.py`
- `tests/test_command_service.py`
- `tests/test_integration.py`
- `tests/test_imports.py`

### 실제로 부딪힌 문제

1. Python 3.9 타입 힌트 호환성
2. `cmd` 패키지 이름 충돌
3. 샌드박스의 포트 바인딩 제한

### 배운 점

구현은 코드만 잘 짠다고 끝나지 않는다.  
버전 호환성, 실행 환경, 테스트 방식도 설계의 일부다.

## Entry 6. 지금 이 구현의 상태

### 현재 가능한 것

- 서버 실행
- CLI로 단일 명령 실행
- `HELLO 3`, `SET`, `GET`, `DEL`, `EXPIRE`, `TTL`
- lazy expiration
- background expiration sweep
- protocol / service / integration 테스트

### 아직 하지 않은 것

- 영속성
- 자료구조 확장(`Hash`, `List`, `Set`, `Sorted Set`)
- 더 정교한 동시성 모델
- 운영 수준의 로깅/메트릭

### 다음에 확장한다면

1. `SET key value EX seconds`
2. `EXISTS`
3. `KEYS pattern`
4. 자료구조 확장
