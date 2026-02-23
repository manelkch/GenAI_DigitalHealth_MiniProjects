
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

    return file

def write_file(path: str, code_to_write):
    with open(f'{path}', 'w') as f:
        f.write(code_to_write)
    return True

def run_python_script(file_name:str):
   result = subprocess.run(["python", file_name], capture_output=True, text=True)
   print(result.stdout.strip())


def stop():
    exit

def get_available_function_for_llm() -> dict:
    functions = {
       "write_file": {
           "function": write_file,
           "documentation": 
           {
            "function_name" : "write_file",
            "signature": "write_file(path: str, content: str)",
            "parameters" : ["path", "code to write"],
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
            "signature": "read_file(path: str) -> str",
            "parameters" : ["path"],
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
            "signature": "run_python_script(file_name: str)",
            "parameters" : ["file_name"],
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
            "signature": "stop()",
            "parameters" : [],
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

'''
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
'''

def extract_json_from_model_output(text):
    cleaned = re.sub(r"```json|```", "", text).strip()

    match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output:\n" + text)
    
    json_like = match.group(1).strip()
    
    try:

        data = json.loads(json_like)
        return data
    except json.JSONDecodeError as e_json:
 
        try:
            data = ast.literal_eval(json_like)
            return data
        except Exception as e_ast:
            raise ValueError(f"Model output is neither valid JSON nor Python literal:\n{json_like}") from e_ast


def llm_tasks_plan(prompt: str, available_functions: dict):
    available_docs = get_function_documentations(available_functions)
    str_function_docs = str(available_docs)

    system_prompt = f"""
    You are a task planner. Break down the user's request into a concise list of sequential steps that can be solved by calling the available functions.
    The available function you can use are : {str_function_docs}
    Focus on the minimum steps required.

    User Query: "{prompt}"

    Return the plan as a JSON dict with task number as key and task description as item, as following:

        {{
          "1": "Write the Python code containing the 'afficher' function that prints 'bjr' to the file 'bjr.py'.",
          "2": "Execute the file 'bjr.py' to test the function."
        }}
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

    tasks = extract_json_from_model_output(content)
    print(tasks)

    return tasks

  
def llm_function_call(prompt: str, available_functions: dict):

    available_docs = get_function_documentations(available_functions)
    str_function_docs = str(available_docs)

    '''
    system_prompt = f"""
    You must perform a task given by a fellow Human or AI
    you must tell what function you would like to call as a next step
    The available function you can use are : {str_function_docs}
    Return the function to call in a json format as follow:

        {{
          "function_name": str,
          "parameters": list,
          "next_action_summary": str
        }}

    next_action_summary is a comment about your next action for human review
    the task to do is described in : {prompt}
    """
    '''
    system_prompt = f"""
    You are an intelligent agent that executes one step at a time.
    Your goal is to perform the task described below using *one* of the available functions as the next step.
    The available function documentation is: {str_function_docs}
    
    **Current Task**: {prompt}

    Return ONLY a single, valid JSON object following this strict format:

        {{
          "function_name": str,
          "parameters": list,
          "next_action_summary": str
        }}
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

    function_call_dict = extract_json_from_model_output(function_call_json)

    print(f"I am about to do : {function_call_dict['next_action_summary']}")

    function_name:str = function_call_dict["function_name"]
    function_parameters = function_call_dict["parameters"]

    function_to_call = available_functions[function_name]["function"]
    print(function_to_call)
    
    try:
       result = function_to_call(*function_parameters)
       return True, function_name, result, function_call_dict['next_action_summary']
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
    previous_results = []
    while stop:
        prompt = input('Comment puis-je vous aider ?\n')
        tasks = llm_tasks_plan(prompt, function_avails)
        for nb_task, task in tasks.items():
            task_prompt = f"user_request : {prompt}, task to perform : {task}"
            try:
                feedback, fonction_name, result, action_summary = llm_function_call(task_prompt, function_avails)
                if feedback:
                    if fonction_name == "stop":
                        break
                    else:
                        previous_results.append(action_summary)
                        continue
                else:
                    feedback, fonction_name, result, action_summary = llm_function_call(f'{task_prompt} previous result : {result}', function_avails)
            except Exception as e:
                print(f"An exception occurred: {e}")

            
            print(f"List of previous results : {previous_results}")

            

agent_execute()