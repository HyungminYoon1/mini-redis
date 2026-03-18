# Store And TTL

## 왜 저장소를 두 개로 나눴는가

이 프로젝트는 아래 두 저장소를 분리했다.

- value 저장소: `key -> value`
- TTL 저장소: `key -> expires_at`

이렇게 나누면 `EXPIRE`가 값을 바꾸는 명령이 아니라 메타데이터를 바꾸는 명령이라는 사실이 잘 보인다.

## 핵심 파일

- `internal/repository/in_memory_store.py`
- `internal/repository/in_memory_ttl.py`
- `internal/expiration/expiration_manager.py`
- `internal/expiration/expiration_sweeper.py`
- `internal/expiration/ttl_calculator.py`

## `SET`

`SET key value`는 두 가지를 한다.

1. value 저장소에 값을 넣는다
2. 기존 TTL이 있으면 제거한다

왜 TTL을 제거할까?  
Redis에서 `SET`은 보통 기존 값을 덮어쓰는 의미이기 때문에, 이전 만료 메타데이터까지 그대로 두면 의도하지 않은 만료가 발생할 수 있다.

## `GET`

`GET`은 바로 값을 읽지 않는다. 먼저 만료 여부를 확인한다.

순서:

1. `purge_if_expired(key)`
2. value 조회
3. 없으면 null, 있으면 blob string 반환

이게 "lazy expiration"이다. 접근 시점에 만료를 정리하는 방식이다.

## `DEL`

`DEL`은 value와 TTL 메타데이터를 함께 정리한다.

여기서 중요한 건 "만료 상태였다면 이미 없는 key처럼 취급"하는 점이다. 그래서 먼저 `purge_if_expired`를 호출한다.

## `EXPIRE`

`EXPIRE key seconds`는 존재하는 key에만 TTL을 준다.

- key가 없으면 `0`
- key가 있으면 `1`

이 명령은 value를 바꾸지 않고 TTL 저장소만 갱신한다.

## `TTL`

`TTL key`는 세 가지 상태를 구분해서 보는 연습이다.

- key 자체가 없으면 `-2`
- key는 있지만 TTL이 없으면 `-1`
- TTL이 있으면 남은 초

이 구분은 Redis를 이해할 때 매우 중요하다. "key 없음"과 "TTL 없음"은 다른 상태다.

## lazy expiration vs background sweep

### lazy expiration

장점:

- 구현이 단순하다
- 정확성이 좋다

단점:

- 아무도 접근하지 않는 만료 key는 메모리에 남을 수 있다

### background sweep

장점:

- 접근이 없는 만료 key도 정리할 수 있다

단점:

- 추가 스레드와 주기 관리가 필요하다

이 프로젝트는 둘 다 넣었다.  
Redis도 내부적으로 비슷한 문제를 해결해야 한다는 점을 느끼는 것이 학습 포인트다.
