# Project Map

## 상위 구조

이 프로젝트는 크게 3층으로 나뉜다.

- `cmd/`
  - 사용자와 직접 맞닿는 실행 진입점
- `internal/`
  - 실제 서버, 프로토콜, 명령, 저장소 로직
- `tests/`
  - 표준 라이브러리 `unittest` 기반 검증 코드

## 폴더별 역할

### `cmd/mini_redis_server`

서버 실행 진입점이다.

- 기본 설정 로드
- CLI 인자 `--host`, `--port` 해석
- `MiniRedisServer` 생성 및 실행

### `cmd/mini_redis_cli`

단일 명령을 보내는 클라이언트다.

- 서버 접속
- `HELLO 3` 선전송
- 사용자 명령을 RESP Array로 만들어 전송
- 응답을 사람이 읽기 쉬운 형태로 출력

### `internal/protocol/resp`

RESP3를 다룬다.

- `types.py`
  - RESP 값을 내부 모델로 표현
- `request_decoder.py`
  - 바이트를 RESP 값으로 복원
- `response_encoder.py`
  - RESP 값을 바이트로 직렬화
- `socket_io.py`
  - 소켓에서 "RESP 프레임 하나"를 읽는 도우미
- `hello_handler.py`
  - `HELLO 3` 응답 생성

### `internal/command`

명령을 "프로토콜 값"에서 "비즈니스 명령"으로 바꾼다.

- `parser.py`
  - RESP Array를 `Command(name, arguments)`로 변환
- `validator.py`
  - 지원 명령인지, 인자 수와 타입이 맞는지 검사
- `command.py`
  - 내부 명령 모델

### `internal/service`

각 명령의 실제 의미를 구현한다.

- `set_service.py`
  - 값 저장, 기존 TTL 제거
- `get_service.py`
  - 접근 시 만료 확인 후 값 반환
- `del_service.py`
  - 값과 TTL 메타데이터 삭제
- `expire_service.py`
  - TTL 설정
- `ttl_service.py`
  - 남은 TTL 계산
- `command_service.py`
  - 각 명령 서비스를 한 곳에서 dispatch

### `internal/repository`

실제 메모리 저장소다.

- `in_memory_store.py`
  - `key -> value`
- `in_memory_ttl.py`
  - `key -> expires_at`

중요한 점은 value와 TTL이 분리되어 있다는 것이다. Redis의 내부 구현은 훨씬 복잡하지만, 학습용으로는 이 분리가 TTL의 의미를 이해하는 데 큰 도움이 된다.

### `internal/expiration`

TTL 만료 정책을 담당한다.

- `expiration_manager.py`
  - 어떤 key가 지금 만료됐는지 판단하고 즉시 제거
- `expiration_sweeper.py`
  - 접근이 없는 만료 key도 주기적으로 정리
- `ttl_calculator.py`
  - 남은 TTL 계산

### `internal/server`

TCP 서버와 세션 처리다.

- `server.py`
  - 소켓 listen, 연결 수락, sweeper 실행, 세션 생성
- `session_handler.py`
  - 연결 하나의 요청/응답 루프
- `shutdown.py`
  - 서버 종료 진입점

## 가장 중요한 흐름

이 프로젝트는 결국 아래 한 줄로 요약된다.

`socket bytes -> RESP decode -> Command parse -> validate -> execute -> RESP encode -> socket bytes`

이 흐름을 이해하면 Redis-like 서버의 핵심을 거의 다 잡은 것이다.
