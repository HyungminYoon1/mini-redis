# Mini Redis Reading Guide

이 폴더는 "무엇을 만들었는가"보다 "왜 이렇게 만들었는가"를 이해하기 위한 학습 문서다.

이 프로젝트를 읽는 추천 순서는 아래와 같다.

1. `01-project-map.md`
2. `02-resp3.md`
3. `03-command-pipeline.md`
4. `04-store-and-ttl.md`
5. `05-server-and-cli.md`
6. `06-tests-and-debugging.md`
7. `99-dev-journal.md`

## 이 프로젝트에서 배우려는 것

- Redis가 왜 단순한 key-value 저장소처럼 보이지만, 실제로는 프로토콜과 명령 실행 파이프라인이 중요한지
- RESP3가 서버와 클라이언트 사이의 계약으로 어떻게 동작하는지
- `SET`, `GET`, `DEL`, `EXPIRE`, `TTL` 같은 명령이 저장소와 TTL 메타데이터를 어떻게 바꾸는지
- 서버가 소켓 연결, 요청 파싱, 명령 실행, 응답 직렬화를 어떻게 이어 붙이는지

## 이 구현의 범위

이 구현은 학습용 mini-redis다.

- 문자열 key / 문자열 value만 지원
- 인메모리 저장만 지원
- 영속성 없음
- `HELLO 3`, `SET`, `GET`, `DEL`, `EXPIRE`, `TTL` 지원
- CLI는 단일 명령 실행 방식

## 빠른 실행

서버 실행:

```bash
python3 cmd/mini_redis_server/main.py --host 127.0.0.1 --port 6379
```

CLI 실행:

```bash
python3 cmd/mini_redis_cli/main.py --host 127.0.0.1 --port 6379 SET mykey hello
python3 cmd/mini_redis_cli/main.py --host 127.0.0.1 --port 6379 GET mykey
```

테스트 실행:

```bash
PYTHONPYCACHEPREFIX=/tmp/python-cache python3 -m unittest discover -s tests -v
```

## 읽을 때 붙잡아야 할 질문

- 왜 `HELLO 3`을 먼저 보내는가?
- 왜 parser, validator, service를 분리했는가?
- 왜 value 저장소와 TTL 저장소를 분리했는가?
- 왜 만료 처리를 "접근 시 삭제"와 "백그라운드 sweep" 두 방식으로 나눴는가?
- 왜 CLI는 사람이 읽기 쉬운 문자열을 출력하고, 내부에서는 RESP 값을 유지하는가?
