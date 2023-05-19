# spectrometerFocusController

스펙트로미터 포커싱 알고리즘을 포함한 제어 모듈

## Signals

    - initFocusingSignal()
    - alreadyRunningSignal()
    - alreadyStoppedSignal()
    - errDevicePosition(str)
    - errFocusingFailed(str)
    - focusCompleteSignal(list, int)

    - reqDeviceConnected()
    - reqConnectedDevice()
    - reqMoveDevice(float)
    - reqStopDevice()

#### initFocusingSignal()
  
- 포커싱 알고리즘 초기화가 완료되었음을 알림

#### alreadyRunningSignal()

- 이미 작동중임을 알림

#### alreadyStoppedSignal()

- 이미 정지상태임을 알림

#### errDevicePosition(str)

- 알고리즘상 기기의 위치가 옳바르지 않음을 에러 내용과 함께 전달

#### errFocusingFailed(str)

- 포커싱 실패를 에러 내용과 함께 전달

#### focusCompleteSignal(list, int)

- 포커스가 완료되었음을 알리고, 마지막 라운드의 스펙트럼 데이터와 초점 포지션의 idx를 전달함

#### reqDeviceConnected()

- 기기 연결 확인 요청

#### reqConnectedDevice()

- 기기 연결 요청

#### reqMoveDevce(float)

- 기기를 전달되는 좌표로 이동할 것을 요청

#### reqStopDevice()

- 기기 정지 요청

## Slots

    - resumeFocusing()
    - pauseFocusing()
    - restartFocusing()

    - onResDeviceConnected(bool)
    - onResStopDevice()
    - onResMoveDevice()

#### resumeFocusing()

- 포커싱 시작, pause 상태인 경우 중지 지점부터 재개

#### pauseFocusing()

- 포커싱 중지

#### restartFocusing()

- running, pause 상태와 상관없이 처음부터 재시작

#### onResDeviceConnected(bool)

- 디바이스 연결 확인 응답에 대한 처리

#### onResMoveDevice()

- 기기 이동요청 응답시 처리

#### onResStopDevice()

- 기기 중단요청 응답시 처리