from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import re
import ast
from mistralai import Mistral


# ********* Available Functions for the LLM *********


def make_web_research(query: str) -> list[str]:

    load_dotenv()

    SERP_API_KEY = os.getenv("SERP_API_KEY")

    params = {
    "engine": "google",
    "q": f"{query}",
    "api_key": f"{SERP_API_KEY}"
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results["organic_results"]

    return organic_results


def visit_web_page(url: str) -> str:

    r = requests.get(url)
    print(r.content)

    return extract_content_html(r.content)


def extract_content_html(html_content : str) -> str:
    soup = BeautifulSoup(html_content, features="html.parser")

    # remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()   

    # get text
    text = soup.get_text()

    # break into lines 
    lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    print(text)
    return text


def stop():
    exit


# ********* Get available Functions for the LLM *********


def get_available_function_for_llm() -> dict:
    functions = {
       "make_web_research": {
           "function": make_web_research,
           "documentation": 
           {
            "function_name" : "make_web_research",
            "parameters" : ["query"],
            "signature": "make_web_research(query: str) -> list[str]",
            "description": "allows to make a web research on Google Search",
            "examples": [
                    {
                        "code": "make_web_research('I want to know the clinical guidlines in Europe for all the chronic diseases')"
                    },
                    {
                        "code": "make_web_research('I want to know the clinical guidlines in US for diabetes')"
                    },
                    {
                        "code": "make_web_research('A patient has cough and fever, what is the disease assiciated with these symptoms ?')"
                    }
                ]
           }
        },
        "visit_web_page": {
           "function": visit_web_page,
           "documentation": 
           {
            "function_name" : "visit_web_page",
            "parameters" : ["url"],
            "signature": "visit_web_page(url: str) -> str",
            "description": "allows to visit a web page from a given url",
            "examples": [
                    {
                        "code": "visit_web_page('https://library.chamberlain.edu/findingclinicalpracticeguidelines')"
                    },
                    {
                        "code": "visit_web_page('https://www.has-sante.fr/jcms/c_431294/en/clinical-practice-guidelines-cpg')"
                    },
                    {
                        "code": "visit_web_page('https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines')"
                    }
                ]
           }
        },
        "extract_content_html": {
           "function": extract_content_html,
           "documentation": 
           {
            "function_name" : "extract_content_html",
            "parameters" : ["file_name"],
            "signature": "extract_content_html(html_content : str) -> str",
            "description": "allows to extract the content of an html document",
            "examples": [
                    {
                        "code": "extract_content_html(html_page_content)"
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


# ********* LLM Call *********


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
  
    #print(f' params : {function_parameters}\n')
    function_to_call = available_functions[function_name]["function"]
    #print(f'function to call : {function_to_call}\n')
    
    try:
       result = function_to_call(*function_parameters)
       return True, function_name, result
    except:
        print("An exception occurred")
        return False


def agent_execute():
    stop = True
    function_avails = get_available_function_for_llm()
    while stop:
        prompt = input('Comment puis-je vous aider ?\n')
        
        feedback, fct, res = llm_function_call(prompt, function_avails)
        if feedback:
            if fct == "stop":
                break
            else:
                print(fct)
                print(res)
        else:
            feedback, fct, res = llm_function_call(f'{prompt} previous result : {res}', function_avails)
        
        print(fct)
        


agent_execute()