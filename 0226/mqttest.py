import paho.mqtt.client as mqtt

# 브로커(서버)에 접속했을 때 자동으로 실행되는 콜백 함수 정의
def on_connect(client, userdata, flags, rc):
    # rc(Result Code)는 접속 결과를 의미합니다 (0이면 성공).
    print("Connected with result code " + str(rc))
    # 접속에 성공하면 "test"라는 토픽(주제)을 구독(Subscribe)합니다.
    # 이제 이 토픽으로 들어오는 메시지를 이 클라이언트가 받을 수 있습니다.
    client.subscribe("device/05/temperature", 1)

# 구독 중인 토픽에서 메시지가 왔을 때 자동으로 실행되는 콜백 함수 정의
def on_message(client, userdata, msg):
    # msg.topic: 메시지가 온 토픽 이름
    # msg.payload: 전송된 실제 데이터 (바이트 형태이므로 str()을 씌워 출력하거나 .decode()를 사용함)
    print(msg.topic + ": "+str(msg.payload))

# 1. MQTT 클라이언트 객체를 생성합니다.
client = mqtt.Client()

# 2. 위에서 정의한 콜백 함수들을 클라이언트 객체에 등록(연결)합니다.
client.on_connect = on_connect
client.on_message = on_message

# 3. 브로커(서버)에 연결을 시도합니다.
# "127.0.0.1": 서버 주소 (현재 컴퓨터), 1883: MQTT 표준 포트, 60: 접속 유지 시간(Keep Alive)
client.connect("127.0.0.1", 1883, 60)

# 4. 네트워크 루프를 무한히 실행합니다.
# 이 함수가 실행되는 동안 클라이언트는 배경에서 계속 서버와 통신하며 메시지를 기다립니다.
# (이 줄 아래의 코드는 실행되지 않는 '무한 대기' 상태가 됩니다.)
client.loop_forever()