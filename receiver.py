#!/usr/bin/env python
import RPi.GPIO as GPIO
import time
from datetime import datetime
from PCF8591 import PCF8591
import requests
import json
from ast import literal_eval

API_SERVER_URL = 'http://192.168.0.71:5000'

# 포토레지스터 모듈
class LaserMeasure(object):
    def __init__(self, addr=0x48, device_num=0):
        # PCF8591_MODULE SETUP
        self.PCF8591_MODULE = PCF8591.PCF8591()
        # SET GPIO WARNINGS AS FALSE
        GPIO.setwarnings(False)
        # SET DEVICE ID
        self.device_id = device_num

    def get_object_detected(self):
        value = self.PCF8591_MODULE.read(2)
        # 값은 환경에 따라 변경 필요
        return value > 30

    def destroy(self):
        GPIO.cleanup()


def main():
    try:
        # Init
        receiver = LaserMeasure(0x48, 0)
        before_status = False
        current_job = 0

        temp = requests.get(API_SERVER_URL + '/getid').text
        car_id = int(temp.rstrip())

        last_update = time.time()
        last_log = time.time()
        while True:
            if time.time() - last_update > 2:
                temp = int(requests.get(API_SERVER_URL + '/getid').text.rstrip())
                if car_id != temp:
                    if temp != -1 and current_job == 0:
                        print(str(temp) + "번 차량 출발")
                    elif car_id != -1 and temp == -1 and current_job != 0:
                        print(str(car_id) + "번 차량 실격")
                        current_job = 0
                    car_id = temp
                    
                last_update = time.time()
                
            sensor_value = receiver.get_object_detected()
            log_timestamp = time.time()
            if log_timestamp - last_log > 1:
                print("현재 센서 측정 결과:", "감지됨" if sensor_value else "감지 안됨")
                last_log = log_timestamp
            if sensor_value and car_id != -1:
                # 연속으로 감지되지 않는 상황에서
                if not before_status:
                    # 감지되었다고 체크
                    before_status = True
                    # 시작 지점 체크 -> 서버에 측정중이라고 체크
                    if current_job == 0:
                        res = requests.post(API_SERVER_URL + "/status", {"status": "1"})
                        print("Start LapTime Check Result:", literal_eval(res.text)["result"])
                    # 현재 시간
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    print("통과 시각:", current_time)
                    # 타임스탬프 DB에 업데이트
                    res = requests.post(API_SERVER_URL + '/settime', {"car_id": str(car_id), "cur_job": str(current_job), "timestamp": current_time})
                    print("Update Time Result:", literal_eval(res.text)["result"])
                    # 만약 세바퀴를 다 돌았다면
                    if current_job == 3:
                        # 서버에 측정이 끝났다고 체크
                        res = requests.post(API_SERVER_URL + "/status", {"status": "0"})
                        print("Finish LapTime Check Result:", literal_eval(res.text)["result"])

                        # 주행 완료
                        current_job = 0
                        print(str(car_id) + "번 차량 주행 완료")
                        res = requests.post(API_SERVER_URL + '/setfinished')
                        print("Finish Check Result:", literal_eval(res.text)["result"])
                        
                        print("현재 센서 측정 결과:", "감지됨" if receiver.get_object_detected() else "감지 안됨")
                        final_lap_last_log = time.time()
                        log_cnt = 0
                        while log_cnt < 3:
                            final_lap_log_timestamp = time.time()
                            if final_lap_log_timestamp - final_lap_last_log > 1:
                                print("현재 센서 측정 결과:", "감지됨" if receiver.get_object_detected() else "감지 안됨")
                                log_cnt += 1
                                final_lap_last_log = final_lap_log_timestamp
                    else:
                        current_job += 1
                        # 3초 이후에 랩타임 다시 체크
                        time.sleep(3)

            else:
                before_status = False

            time.sleep(0.005)

    # 종료
    except KeyboardInterrupt:
        receiver.destroy()


if __name__ == '__main__':
    main()
