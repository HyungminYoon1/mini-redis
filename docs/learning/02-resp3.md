# RESP3

## RESP가 왜 필요한가

Redis는 "문자열 몇 개 주고받는 서버"가 아니다. 클라이언트와 서버가 서로 같은 방식으로 메시지를 이해해야 한다. RESP는 그 약속이다.

예를 들어 `SET mykey hello`는 내부적으로 단순한 공백 문자열이 아니라, 길이와 타입이 포함된 배열 형태로 전송된다.

```text
*3
$3
SET
$5
mykey
$5
hello
```

이런 구조 덕분에 공백이나 개행이 들어간 값도 정확히 전송할 수 있다.

## 이 프로젝트에서 지원한 RESP 타입

- Simple String
- Blob String
- Number
- Null
- Error
- Array
- Map

이 중 핵심은 Array다. 요청은 거의 항상 Array로 들어오기 때문이다.

## 구현 포인트

### `types.py`

`RespValue(kind, value)`는 RESP 값을 내부에서 통일된 형태로 표현한다.

예:

- `simple_string("OK")`
- `blob_string("hello")`
- `number(3)`
- `null()`
- `array([...])`

이 모델을 쓰면 디코더와 인코더가 같은 공통 언어를 공유한다.

### `request_decoder.py`

디코더는 바이트의 첫 글자를 보고 타입을 판단한다.

- `+`면 Simple String
- `$`면 Blob String
- `:`면 Number
- `*`면 Array
- `%`면 Map
- `_`면 Null
- `-`면 Error

중요한 학습 포인트는 "네트워크 데이터는 한 번에 다 오지 않을 수 있다"는 점이다.  
그래서 디코더는 불완전한 데이터와 잘못된 데이터를 구분해야 한다.

- 데이터가 덜 왔으면 `IncompleteRespError`
- 형식이 틀렸으면 `RespProtocolError`

이 구분 덕분에 소켓 읽기 루프가 "조금 더 읽어야 하는지", "에러 응답을 보내야 하는지"를 판단할 수 있다.

### `socket_io.py`

이 파일은 소켓에서 `recv()`를 반복하면서 "RESP 메시지 하나"가 완성될 때까지 버퍼를 모은다.

이 계층을 따로 둔 이유는 다음과 같다.

- 서버 세션 처리기와 CLI가 같은 읽기 방식을 재사용할 수 있다
- 디코더는 바이트 해석만 담당하고, 소켓 I/O는 버퍼링만 담당한다

### `response_encoder.py`

인코더는 내부 RESP 값을 다시 바이트로 만든다.

이 파일을 보면 RESP가 사실상 "재귀적 자료구조 직렬화"라는 걸 이해할 수 있다.

- 단순 값은 한 줄로 직렬화
- Array는 길이를 적고 각 원소를 재귀적으로 직렬화
- Map도 key/value를 순서대로 직렬화

## 초보자가 여기서 꼭 이해해야 할 것

- Redis 프로토콜은 문자열 처리 문제가 아니라 "자료구조 직렬화" 문제다
- 디코딩과 소켓 읽기는 별개의 책임이다
- `HELLO 3`도 결국 RESP Array 요청일 뿐이다
