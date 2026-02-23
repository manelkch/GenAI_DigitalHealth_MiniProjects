
from dotenv import load_dotenv
import os
from mistralai import Mistral
import json
import subprocess
import re
import ast
import sys

def read_file(path: str) -> str:
    with open(f'{path}', 'r') as f:
        file = f.read()
    print(file)

    return file

def write_file(path: str, code_to_write):
    with open(f'{path}', 'w') as f:
        f.write(code_to_write)

def run_python_script(file_name:str):
   result = subprocess.run(["python", file_name], capture_output=True, text=True)

   return result.stdout

def stop():
    exit

def get_available_function_for_llm() -> dict:
    functions = {
       "write_file": {
           "function": write_file,
           "documentation": 
           {
            "function_name" : "write_file",
            "parameters" : ["path", "code to write"],
            "signature": "write_file(path: str, content: str)",
            "description": "allows to write a string a file on the disk",
            "examples": [
                    {
                        "code": "write_file('script1.py', 'print(\"Hello from script 1!\")')"
                    },
                    {
                        "code": "write_file('math_utils.py', 'def add(a, b):\\n    return a + b')"
                    },
                    {
                        "code": "write_file('app.py', 'from math_utils import add\\nprint(add(2, 3))')"
                    }
                ]
           }
        },
        "read_file": {
           "function": read_file,
           "documentation": 
           {
            "function_name" : "read_file",
            "parameters" : ["path"],
            "signature": "read_file(path: str) -> str",
            "description": "allows to read a file on the disk",
            "examples": [
                    {
                        "code": "read_file('script1.py')"
                    },
                    {
                        "code": "read_file('math_utils.py')"
                    },
                    {
                        "code": "read_file('app.py')"
                    }
                ]
           }
        },
        "run_python_script": {
           "function": run_python_script,
           "documentation": 
           {
            "function_name" : "run_python_script",
            "parameters" : ["file_name"],
            "signature": "run_python_script(file_name: str)",
            "description": "allows to execute a python file",
            "examples": [
                    {
                        "code": "run_python_script('script1.py')"
                    },
                    {
                        "code": "run_python_script('math_utils.py')"
                    },
                    {
                        "code": "run_python_script('app.py')"
                    }
                ]
           }
        },
        "stop": {
           "function": stop,
           "documentation": 
           {
            "function_name" : "stop",
            "parameters" : [],
            "signature": "stop()",
            "description": "stop the program",
            "examples": [
                    {
                        "code": "stop()"
                    }
                ]
           }
        }
    }
    return functions

def get_function_documentations(available_functions) -> list:

    result = []

    for func_dict in available_functions.values():

        result.append(func_dict["documentation"])

    return result

# Removes markdown blocks and extracts the first valid JSON object.
def extract_json_from_model_output(text):
    # Remove ```json and ```
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Extract the first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output:\n" + text)

    json_like = match.group(0)

    try:
        # Safely evaluate Python-style dict into a Python dict
        data = ast.literal_eval(json_like)
    except Exception as e:
        raise ValueError(f"Model output is not valid JSON or Python literal:\n{json_like}") from e

    return data


def llm_tasks_plan(prompt: str, available_functions: dict):
    available_docs = get_function_documentations(available_functions)
    str_function_docs = str(available_docs)

    system_prompt = f"""
    extract the different tasks to do in this query: {prompt}
    The available function you can use are : {str_function_docs}
    You must return a list of dict that describes each function to use for each task by using the following structure for each task :
    Return the function to call in a json format as follow:

        {{
          "function_name": str,
          "parameters": list,
          "next_action_summary": str,
          "file_created":list[str]
        }}

    next_action_summary is a comment about your next action for human review
    """

    # LLM PART
    load_dotenv()

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-tiny"

    client = Mistral(api_key=MISTRAL_API_KEY)

    # LLM CALL
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": system_prompt}]
    )

    content = response.choices[0].message.content
    print(content)
    #function_call_dict = json.loads(function_call_json)
    #function_call_dict = extract_json_from_model_output(function_call_json)
    #print(f'dict :{function_call_dict}\n')

    
def llm_function_call(prompt: str, available_functions: dict):

    available_docs = get_function_documentations(available_functions)
    str_function_docs = str(available_docs)

    system_prompt = f"""
    You must perform a task given a fellow Human or AI
    you must tell what function you would like to call as a next step
    The available function you can use are : {str_function_docs}
    Return the function to call in a json format as follow:

        {{
          "function_name": str,
          "parameters": list,
          "next_action_summary": str,
          "file_created":list[str]
        }}

    next_action_summary is a comment about your next action for human review
    the task to do is: {prompt}
    """

    # LLM PART
    load_dotenv()

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-tiny"

    client = Mistral(api_key=MISTRAL_API_KEY)

    # LLM CALL
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": system_prompt}]
    )

    function_call_json = response.choices[0].message.content
    #print(f'json :{function_call_json}\n')
    #function_call_dict = json.loads(function_call_json)
    function_call_dict = extract_json_from_model_output(function_call_json)
    #print(f'dict :{function_call_dict}\n')

    print(f"I am about to do : {function_call_dict['next_action_summary']}")

    function_name:str = function_call_dict["function_name"]
    function_parameters = function_call_dict["parameters"]
    file_created = function_call_dict["file_created"]
    #print(f' params : {function_parameters}\n')
    function_to_call = available_functions[function_name]["function"]
    #print(f'function to call : {function_to_call}\n')
    
    try:
       result = function_to_call(*function_parameters)
       return True, function_name, file_created,result
    except:
        print("An exception occurred")
        return False


'''
def function_calling(prompt: str, available_function: list[str]):

    system_prompt = f""" You must perform a task given by a human, you must tell what function you would like to call as a next step the available function you can use are : {available_function} return the function to call in a json format as follow:

    the task is : {prompt}
    """
    # LLM PART
    load_dotenv()

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MODEL = "mistral-tiny"

    client = Mistral(api_key=MISTRAL_API_KEY)

    # LLM CALL
    response = client.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": system_prompt}]
    )

    result_json = response.choices[0].message.content

    print(result_json)

    result_dict = json.loads(result_json)

    function_name = result_dict["function_name"]
    function_params = result_dict["params"]

    # call the function    

'''

def agent_execute():
    stop = True
    function_avails = get_available_function_for_llm()
    while stop:
        prompt = input('Comment puis-je vous aider ?\n')
        #llm_tasks_plan(prompt, function_avails)
        feedback, fct, file, res = llm_function_call(prompt, function_avails)
        if feedback:
            if fct == "stop":
                break
            else:
                continue
        else:
            feedback, fct, file, res = llm_function_call(f'{prompt} previous result : {res}', function_avails)
        
        print(fct)
        if file:
            print(file)
            run_python_script(file[0])
        

agent_execute()