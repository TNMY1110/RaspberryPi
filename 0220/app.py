import threading
import serial
import time
import mysql.connector
from flask import Flask, render_template

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="test1234",
        database="sensor_db"
    )

def read_sensor():
    try:
        ser = serial.Serial("/dev/ttyUSB1", 9600, timeout=2)
        time.sleep(2)
        line = ser.readline().decode("utf-8").strip()
        ser.close()
        parts = line.split(",")

        return {
            "humidity":    float(parts[0]),
            "temperature": float(parts[1])
        }

    except Exception as e:
        print("센서 오류:", e)
        return {"temperature": None, "humidity": None}

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

def auto_collect(interval=10): # interval초마다 자동 저장
    while True:
        data = read_sensor()
        if data:
            save_to_db(data["temperature"], data["humidity"])
            print(f"저장됨: {data['temperature']}°C, {data['humidity']}%")

        time.sleep(interval)


@app.route('/')
def index():
    records = get_records()
    return render_template("index.html", records=records)

@app.route('/collect')
def collect():
    data = read_sensor()
    if data:
        save_to_db(data["temperature"], data["humidity"])
        return f"저장 완료: 온도 {data['temperature']}°C, 습도 {data['humidity']}%"

    else:
        return "센서 데이터를 읽을 수 없습니다.", 500

thread = threading.Thread(target=auto_collect, args=(10,), daemon=True)
thread.start()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
