import time
import math
import random

# =========================================================
# [설정] 센서 연결 여부 선택
# 센서가 아직 없을 때는 True, 센서가 도착해 연결했을 때는 False로 변경하세요.
# =========================================================
SIMULATION_MODE = True  

# [실험 기준값] 차단제를 바르지 않은 빈 유리판의 UV 센서 전압 (V)
V_BASE_UV = 2.5  
# 초기 바탕 온도 (℃)
T_INITIAL = 25.0 

class SunscreenAnalyzer:
    def __init__(self):
        if not SIMULATION_MODE:
            # 실제 센서 PIN 및 I2C 초기화 (센서 도착 후 사용)
            from machine import ADC, Pin, I2C
            self.uv_adc = ADC(26) # GP26 (ADC0) 핀 연결 예시
            self.i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
            # MLX90614, BH1750 초기화 코드 추가 위치
        
        self.start_time = time.time()

    def read_sensors(self, elapsed_min):
        """센서 데이터 수집 함수"""
        if SIMULATION_MODE:
            # ----------------------------------------------------
            # [시뮬레이션] 시간이 지남에 따라 차단제 성능이 떨어지고 
            # 온도가 올라가는 화학적 현상을 가상 데이터로 생성
            # ----------------------------------------------------
            # 시간이 흐를수록 자외선 투과량(전압)이 점차 증가 (차단력 저하)
            uv_voltage = 0.2 + (elapsed_min * 0.03) + random.uniform(-0.02, 0.02)
            uv_voltage = min(uv_voltage, V_BASE_UV) # 최대 기준값으로 제한

            # 유기자차가 자외선을 흡수하여 열로 바꾸는 발열 현상 가상 구현
            # (시간이 지남에 따라 온도가 상승하다가 차단제 파괴 시 정체)
            temp_rise = 8.0 * (1 - math.exp(-elapsed_min / 10.0)) + random.uniform(-0.2, 0.2)
            surface_temp = T_INITIAL + temp_rise

            # 가시광선 조도 (Lux)
            visible_lux = 1200 + random.uniform(-20, 20)

            return uv_voltage, surface_temp, visible_lux
        else:
            # ----------------------------------------------------
            # [실제 센서 측정] (센서 도착 후 동작)
            # ----------------------------------------------------
            # 1. UV 센서 (아날로그 읽기: 0~65535 -> 0~3.3V 환산)
            raw_adc = self.uv_adc.read_u16()
            uv_voltage = (raw_adc / 65535.0) * 3.3
            
            # 2. MLX90614 (I2C 주소 0x5A에서 온도 읽기)
            # (라이브러리 불러와서 측정값 대입)
            surface_temp = 25.0  # mlx.read_object_temp()
            
            # 3. 조도 센서 읽기
            visible_lux = 1000.0
            
            return uv_voltage, surface_temp, visible_lux

    def calculate_metrics(self, uv_vol, temp):
        """수식 연산 (차단율, 온도 변화량, 피부 위험도)"""
        # 1. 자외선 차단율 (%)
        block_rate = (1.0 - (uv_vol / V_BASE_UV)) * 100.0
        block_rate = max(0.0, min(100.0, block_rate)) # 0~100% 범위 제한

        # 2. 온도 변화량 (℃)
        delta_temp = temp - T_INITIAL

        # 3. 피부 위험도 및 상태 진단 (AI/규칙 기반)
        if block_rate >= 80.0:
            status = "SAFE (안전)"
            risk_score = 15
        elif 50.0 <= block_rate < 80.0:
            status = "WARNING (주의 - 차단력 저하)"
            risk_score = 55
        else:
            status = "RE-APPLY REQUIRED (위험 - 즉시 재도포)"
            risk_score = 90

        return block_rate, delta_temp, status, risk_score

# =========================================================
# 메인 실행 루프
# =========================================================
analyzer = SunscreenAnalyzer()
print("=== 자외선 차단제 광화학 분석 시스템 시작 ===")
if SIMULATION_MODE:
    print("[알림] 현재 '시뮬레이션 모드'로 가상 데이터를 가공 중입니다.\n")

simulated_minutes = 0 # 가상 진행 시간 (분)

while True:
    # 센서 값 읽기 (1초마다 5분씩 흐르는 것으로 시뮬레이션)
    uv_v, temp, lux = analyzer.read_sensors(simulated_minutes)
    
    # 지표 계산
    block_rate, delta_t, status, risk = analyzer.calculate_metrics(uv_v, temp)
    
    # 터미널(Thonny 시리얼 모니터) 출력
    print(f"[{simulated_minutes:02d}분 경과]")
    print(f" - UV 센서 전압: {uv_v:.3f} V  -->  UV 차단율: {block_rate:.1f} %")
    print(f" - 표면 온도: {temp:.2f} ℃  (초기 대비 상승: +{delta_t:.2f} ℃)")
    print(f" - 조도: {lux:.0f} Lux")
    print(f" - [진단 결과]: {status} (피부 위험 점수: {risk}/100)")
    print("-" * 50)
    
    # 시뮬레이션 시간 증가 및 루프 대기
    simulated_minutes += 5
    if simulated_minutes > 60:
        simulated_minutes = 0 # 60분 지나면 리셋
        print("\n=== 새로운 실험 세션 시작 ===\n")
        
    time.sleep(2) # 2초마다 갱신
