import threading
import serial
import time
import mysql.connector
from flask import Flask, render_template, request

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="test1234",
        database="sensor_db"
    )

def save_to_db(temperature, humidity):
    conn   = get_connection()
    cursor = conn.cursor()
    sql    = "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)"
    cursor.execute(sql, (temperature, humidity))
    conn.commit()
    cursor.close()
    conn.close()

def get_records(limit=10):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM sensor_data ORDER BY recorded_at DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# def auto_collect(interval=10): # interval초마다 자동 저장
#     while True:
#         data = read_sensor()
#         if data:
#             save_to_db(data["temperature"], data["humidity"])
#             print(f"저장됨: {data['temperature']}°C, {data['humidity']}%")

#         time.sleep(interval)


@app.route('/')
def index():
    records = get_records()
    return render_template("index.html", records=records)

@app.route('/collect')
def collect():
    # 1. 아두이노가 보낸 파라미터 가져오기
    temp_raw = request.args.get('temp')
    humi_raw = request.args.get('humi')

    # 2. 값이 아예 없거나(None), 빈 문자열인지 먼저 체크
    if temp_raw is None or humi_raw is None or temp_raw == "" or humi_raw == "":
        print("경고: 빈 데이터가 수신되었습니다.")
        return "Empty Data", 400

    try:
        # 3. 숫자로 변환 가능한지 확인 (여기서 실패하면 except로 이동)
        temperature = float(temp_raw)
        humidity = float(humi_raw)

        # 4. (선택사항) 센서의 정상 범위를 벗어난 값인지 체크 (예: 온도가 -50 미만 혹은 100 초과)
        if not (-50 < temperature < 100):
            return "Out of Range", 400

        # 5. 모든 검증을 통과했을 때만 DB 저장
        save_to_db(temperature, humidity)
        print(f"저장 성공: {temperature}°C, {humidity}%")
        return "Success", 200

    except ValueError:
        # 숫자가 아닌 문자열(예: "nan")이 들어온 경우 처리
        print(f"에러: 잘못된 숫자 형식 수신 (temp: {temp_raw}, humi: {humi_raw})")
        return "Invalid Number Format", 400

# thread = threading.Thread(target=auto_collect, args=(10,), daemon=True)
# thread.start()

if __name__ == '__main__':
    app.run(host='192.168.0.79', port=5000, debug=True, use_reloader=False)
