functions = [
    {
        "name": "get_weather_forecast",
        "description": "Get weather informations up to 5 hours in the future using an weather API in a given location. Also this can get a current weather information.\
            조금 후의, 혹은 나중의, 이따가, 몇 시간 뒤 등의 날씨 정보가 필요할 때에는 이 함수를 사용해야 한다.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city or dong, e.g. 전주, 금암1동",
                },
            },
            "required": ["location"],
        },
    }
]