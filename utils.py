import yaml
from datetime import datetime
import calendar

def load_yaml(filepath):
    with open(filepath, "r") as f:
        return yaml.full_load(f)
    
def get_current_date_string() -> str:
    current_date = datetime.now().date().strftime("%Y%m%d")
    
    if datetime.now().minute < 45 and datetime.now().hour == 0:
        year = current_date[0: 4]
        month = current_date[4: 6]
        day = current_date[6: ]
        
        if month == "01" and day == "01":
            year = int(year) - 1
            month = 12
            day = get_last_day_of_month(year, month)
        
        elif day == "01":
            year = int(year)
            month = int(month) - 1
            day = get_last_day_of_month(year, month)
            
        else:
            day = int(day) - 1
            
        current_date = f"{year}{month}{day}"
        
    return current_date

def get_current_hour_string() -> str:
    now = datetime.now()
    
    if now.minute<45: # base_time와 base_date 구하는 함수
        if now.hour==0:
            base_time = "2330"
        else:
            pre_hour = now.hour-1
            if pre_hour<10:
                base_time = "0" + str(pre_hour) + "30"
            else:
                base_time = str(pre_hour) + "30"
    else:
        if now.hour < 10:
            base_time = "0" + str(now.hour) + "30"
        else:
            base_time = str(now.hour) + "30"

    return base_time

def get_last_day_of_month(year: int, month: int) -> int:
    last_day = calendar.monthrange(year, month)[1]

    return last_day

def dict_to_str(info: dict) -> str:
    info_str = ""
    
    for key, value in info.items():
        info_str += f"{key}: {value}, "
    info_str = info_str.strip(", ")
    
    return info_str
    

def setting_for_langsmith(OPENAI_API_KEY, LANGCHAIN_API_KEY, config):
    import os
    
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = config["project_name"]
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
if __name__ == "__main__":
    print(get_current_date_string())