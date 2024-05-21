from api_keys import WEATHER_DECODING_API_KEY

import requests
from utils import (get_current_date_string,
                   get_current_hour_string,
                   dict_to_str
)

WEATHER_CHANGED = False

weathercode2text = {
    "T1H": "기온",
    "RN1": "1시간 강수량",
    "SKY": "하늘 상태",
    "REH": "습도",
    "PTY": "강수 형태",
    "LGT": "낙뢰",
    "VEC": "풍향",
    "WSD": "풍속",
    "UUU": "동서바람성분",
    "VVV": "남북바람성분",
}
    
    
def get_weather_forecast(location: str = "전주") -> str:
    """
    Get weather informations up to 5 hours in the future using an weather API in a given location.
    Also this can get a current weather information.
    
    parameter: 
    location - 사용자 지역 정보
    
    return:
    weather_info - model 입력에 포함될 string type의 날씨 정보
    """
    
    raw_weather_info, raw_special_report_info = get_weather_from_api()
    weather_info, special_report_info = filter_weather_info(raw_weather_info, raw_special_report_info, location)
    
    weather_info = dict_to_str(weather_info)
    special_report_info = dict_to_str(special_report_info)
    
    weather_info = weather_info + "\n" + special_report_info
    
    return weather_info
    

def get_weather_from_api() -> list:
    """
    return: 
    raw_weather_info - 기온, 강수량, 하늘상태, 습도, 강수형태, 낙뢰, 풍향, 풍속 등의 날씨 정보
    raw_special_report - 특보 및 주의보 발효된 지역, 시각 등의 정보
    """
    
    # 날씨 api: nx, ny 값으로 지역 설정 필요 - nx, ny 값은 excel 참조
    weather_api_url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
    weather_params ={'serviceKey' : WEATHER_DECODING_API_KEY, 
            'pageNo' : '1', 
            'numOfRows' : '9999', 
            'dataType' : 'JSON', 
            'base_date' : get_current_date_string(), 
            'base_time' : get_current_hour_string(), 
            'nx' : '63', 
            'ny' : '89' }
    
    special_report_api_url = "http://apis.data.go.kr/1360000/WthrWrnInfoService/getPwnStatus"
    special_report_params = {'serviceKey' : WEATHER_DECODING_API_KEY, 
            'pageNo' : '1', 
            'numOfRows' : '9999', 
            'dataType' : 'JSON', 
            }
    
    weather_response = requests.get(url = weather_api_url, params = weather_params)
    special_report_response = requests.get(url = special_report_api_url, params = special_report_params)
    
    raw_weather = weather_response.json()
    raw_special_report = special_report_response.json()

    return raw_weather['response']['body']['items']['item'], raw_special_report['response']['body']['items']['item']


def filter_weather_info(raw_weather_info: list, raw_special_report_info: list, location: str) -> dict:
    """
    parameter:
    raw_weather_info - 기온, 강수량, 하늘상태, 습도, 강수형태, 낙뢰, 풍향, 풍속 등의 날씨 정보
    raw_special_report_info - 특보 및 주의보 발효된 지역, 시각 등의 정보
    location - 사용자 지역 정보
    
    return: 
    filtered_weather_info - model input에 넣을 형태로 filtering된 날씨 정보 ex) {"location": "", "temperature": "섭씨 20°C", ~}
    filtered_special_report_info - model input에 넣을 형태로 filtering된 특보/주의보 정보
    """
    
    filtered_weather_info = {}
    
    for i in range(0, len(raw_weather_info), 6):
        weathercode = raw_weather_info[i]['category']
        weather_value = filter_weather_value(weathercode, raw_weather_info[i]['fcstValue'])
        
        filtered_weather_info[weathercode2text[weathercode]] = weather_value        
        filtered_weather_info = dict(("현재 " + key, value) for key, value in filtered_weather_info.items())
        
    filtered_weather_info.pop("현재 동서바람성분")
    filtered_weather_info.pop("현재 남북바람성분")
    
    # weather
    for i in range(len(raw_weather_info)):
        if i % 6 == 0:
            continue
        
        weathercode = raw_weather_info[i]['category']
        weather_value = filter_weather_value(weathercode, raw_weather_info[i]['fcstValue'])
        
        if weathercode == "SKY" or weathercode == "PTY" or weathercode == "RN1" or weathercode == "WSD" and\
            weather_value != filtered_weather_info[weathercode2text[weathercode]]:
                WEATHER_CHANGED = True
                changed_time = i % 6
                
    # 하늘 상태 or 강수 형태 or 1시간 강수량 or 풍속에 변화가 있으면, 1)현재 날씨와 2)변화가 있는 시간의 날씨 정보를 output           
    if WEATHER_CHANGED:
        changed_weather_info = {}
        
        for i in range(changed_time, len(raw_weather_info), 6):
            weathercode = raw_weather_info[i]['category']
            weather_value = filter_weather_value(weathercode, raw_weather_info[i]['fcstValue'])
            
            changed_weather_info[weathercode2text[weathercode]] = weather_value
            
        changed_weather_info.pop("동서바람성분")
        changed_weather_info.pop("남북바람성분")
        
        changed_weather_info = dict((f"{changed_time}시간 뒤 " + key, value) for key, value in changed_weather_info.items())
        filtered_weather_info.update(changed_weather_info)
            
    # 변화가 없으면, 1)현재 날씨와 2)5시간 뒤의 날씨 정보를 output
    elif not WEATHER_CHANGED:
        after_5hrs_weather_info = {}

        for i in range(5, len(raw_weather_info), 6):
            weathercode = raw_weather_info[i]['category']
            weather_value = filter_weather_value(weathercode, raw_weather_info[i]['fcstValue'])
            
            after_5hrs_weather_info[weathercode2text[weathercode]] = weather_value
            
        after_5hrs_weather_info.pop("동서바람성분")
        after_5hrs_weather_info.pop("남북바람성분")
        
        after_5hrs_weather_info = dict((f"5시간 뒤 " + key, value) for key, value in changed_weather_info.items())
            
        filtered_weather_info.update(after_5hrs_weather_info)
                
    # 특보/주의보
    filtered_special_report_info = {}

    for raw_special_report in raw_special_report_info:
        if location in raw_special_report['t6']:
            filtered_special_report_info["참고사항"] = raw_special_report['other']
            filtered_special_report_info["특보 발효 현황 내용"] = raw_special_report['t6']
            filtered_special_report_info['예비 특보 발효 현황'] = raw_special_report['t7']
            filtered_special_report_info['특보 발효 현황 시각'] = strftime(raw_special_report['tmEf'])
            filtered_special_report_info['발표 시각'] = strftime(raw_special_report['tmFc'])
            
    if len(filtered_special_report_info) == 0:
        filtered_special_report_info["특보 발효 현황 내용"] = location + "에 발효된 특보 및 주의보 없음"
    else:
        for key, value in filtered_special_report_info.items():
            if type(value) == str and value[0] == "o":
                filtered_special_report_info[key] = value.replace("o ", "")
        
    return filtered_weather_info, filtered_special_report_info


def filter_weather_value(weathercode: str, weather_value: str) -> str:
    """
    parameter:
    weathercode - 기상청에서 사용하는 날씨 정보 코드
    weather_value - 날씨 정보
    
    return: 
    weather_value - model input에 넣을 형태로 filtering된 날씨 정보
    """
    if weathercode == "T1H":
        return f"섭씨 {weather_value}°C"
    
    elif weathercode == "RN1":
        return weather_value
   
    elif weathercode == "SKY":
        if weather_value == "1":
            return "맑음"
        elif weather_value == "3":
            return "구름 많음"
        elif weather_value == "4":
            return "흐림"
    
    elif weathercode == "REH":
        return f"{weather_value}%"
    
    elif weathercode == "PTY":
        if weather_value == "0":
            return "맑음"
        elif weather_value == "1":
            return "비가 내림"
        elif weather_value == "2":
            return "비나 눈이 내림"
        elif weather_value == "3":
            return "눈이 내림"
        elif weather_value == "5":
            return "빗방울이 떨어짐"
        elif weather_value == "6":
            return "빗방울이 떨어지거나 눈이 내림"
        elif weather_value == "7":
            return "눈이 내림"
    
    elif weathercode == "LGT":
        if weather_value == "0":
            return "낙뢰 없음"
        else:
            return f"{weather_value}kA의 낙뢰 발생"
    
    elif weathercode == "VEC":
        weather_value = int(weather_value)
        
        if 0 <= weather_value < 45:
            return "북풍/북동풍"
        elif 45 <= weather_value < 90:
            return "북동/동풍"
        elif 90 <= weather_value < 135:
            return "동풍/남동풍"
        elif 135 <= weather_value < 180:
            return "남동품/남풍"
        elif 180 <= weather_value < 225:
            return "남풍/남서풍"
        elif 225 <= weather_value < 270:
            return "남서풍/서풍"
        elif 270 <= weather_value < 315:
            return "서풍/북서풍"
        elif 315 <= weather_value < 360:
            return "북서풍/북풍"
    
    elif weathercode == "WSD":
        weather_value = int(weather_value)
        
        if weather_value < 4:
            return "약한 바람"
        elif 4 <= weather_value < 9:
            return "약간 강한 바람"
        elif 9 <= weather_value < 14:
            return "강한 바람"
        elif 14 <= weather_value:
            return "매우 강한 바람"
        
    elif weathercode == "UUU":
        return f"{weather_value}m/s"
    
    elif weathercode == "VVV":
        return f"{weather_value}m/s"
    
def strftime(datetime: int):
    """
    parameter:
    datetime - int type의 년월일 정보
    
    return: 
    output - string type의 년월일 정보
    """
    datetime = str(datetime)
    
    year = datetime[ :4]
    month = datetime[4: 6]
    day = datetime[6: 8]
    hour = datetime[8: 10]
    minute = datetime[10: ]
    
    output = f"{year}년 {month}월 {day}일 {hour}시 {minute}분"
    
    return output
    
if __name__ == "__main__":
    weather = get_weather_forecast()