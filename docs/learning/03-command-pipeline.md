# Command Pipeline

## 전체 흐름

세션 핸들러에서 요청 하나를 처리하는 흐름은 아래와 같다.

1. 소켓에서 RESP 프레임 읽기
2. RESP Array를 `Command`로 파싱
3. 명령 유효성 검사
4. 비즈니스 로직 실행
5. RESP 응답 직렬화
6. 클라이언트로 전송

이 분리가 중요한 이유는 "문자열 해석"과 "명령 의미"를 섞지 않기 위해서다.

## `parser.py`

파서는 RESP Array를 내부 `Command`로 바꾼다.

예를 들어:

- `["SET", "mykey", "hello"]`
- `Command(name="SET", arguments=["mykey", "hello"])`

이 단계는 아직 "이 명령이 맞는지"를 판단하지 않는다. 형태만 바꾼다.

## `validator.py`

validator는 "형태가 아니라 규칙"을 검사한다.

예:

- 지원하지 않는 명령인가?
- 인자 수가 맞는가?
- `EXPIRE seconds`가 정수인가?
- `seconds > 0`인가?

이 역할을 service 전에 두는 이유는 service를 단순하게 유지하기 위해서다.  
service는 "정상 입력이 들어왔다"는 전제 아래 동작하도록 만드는 편이 읽기 쉽다.

## `command_service.py`

이 파일은 작은 command router다.

- `SET`이면 `SetService`
- `GET`이면 `GetService`
- `DEL`이면 `DelService`
- `EXPIRE`면 `ExpireService`
- `TTL`이면 `TtlService`
- `HELLO`면 `HelloHandler`

즉, parser/validator 다음 단계의 분기점이다.

## 왜 `HELLO 3`을 먼저 강제했는가

세션 핸들러는 `HELLO 3`이 오기 전에는 다른 명령을 거절한다.

이 선택은 교육용으로 의미가 있다.

- RESP3 세션 협상이 실제로 어떤 의미인지 드러난다
- CLI가 왜 handshake를 먼저 보내는지 분명해진다
- "프로토콜 협상"과 "일반 명령"이 같은 파이프라인 위에 있다는 걸 이해할 수 있다

## 초보자가 여기서 꼭 이해해야 할 것

- parser는 번역기
- validator는 문지기
- service는 실제 작업자

이 셋이 분리되면 버그를 고칠 때도 어디를 봐야 하는지 빨라진다.
