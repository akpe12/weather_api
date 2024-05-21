import os
from api_keys import (OPENAI_API_KEY,
                      LANGSMITH_API_KEY
)
import argparse

from langchain_core.output_parsers import StrOutputParser
from models import get_api_model
from prompts.prompter import Prompter
from utils import (load_yaml,
                   setting_for_langsmith,
)

from langsmith import traceable
from functions import functions
from weather import (get_weather_forecast,
)
import json

@traceable
def run(args):
    config = load_yaml(args.config_filepath) # load config
    
    setting_for_langsmith(OPENAI_API_KEY, LANGSMITH_API_KEY, config)
    model = get_api_model(config) # load model

    prompt_templates = load_yaml(config['prompt']['template_path']) # load prompt template
    prompt_template = prompt_templates[config['prompt']['template']]
    prompter = Prompter(config, prompt_template)

    # Load dataset and prompter
    prompt = prompter.get_prompt()

    # Construct a chain
    # LLM 판단 하에 function 적용
    # chain = prompt | model.bind_tools(tools=functions, tool_choice="auto")
    
    # 항상 function 적용
    chain = prompt | model.bind_tools(tools=functions, tool_choice={"type": "function", "function": {"name": "get_weather_forecast"}})
    
    # Invoke a generation
    output = chain.invoke({})
    
    # function 적용 전 output
    print(output)
    
    # function call 적용 부분
    if output.additional_kwargs.get("tool_calls"):
        
        available_functions = {"get_weather_forecast": get_weather_forecast}
        function_name = output.additional_kwargs["tool_calls"][0]["function"]["name"]
        
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(output.additional_kwargs["tool_calls"][0]["function"]["arguments"])
        function_response = fuction_to_call(
                location=function_args.get("location"),
            )
        
        prompt = prompter.get_prompt_for_function(function_response)
        
        function_chain = prompt | model.with_retry() | StrOutputParser()
        output_with_function = function_chain.invoke({})
        
        # function 적용 후 output
        print(output_with_function)
    
    import pdb; pdb.set_trace()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_filepath", default=None, type=str, help="config filepath")
    args = parser.parse_args()

    run(args)