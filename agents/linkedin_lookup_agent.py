'''
implements a function that uses a LangChain Agent to find the LinkedIn URL for a user from their first name and last name
'''
import sys
import os 
from dotenv import load_dotenv 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.tools import get_profile_url_tavily

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool # interfaces that help our LangChain agents/chains or LLMs uses and interact with the external world ex) searching online or a database
from langchain.agents import (
    create_react_agent,
    AgentExecutor 
)
from langchain import hub 

def lookup(name: str) -> str:
    '''
    Receives a name as input and returns a string with that name's LinkedIn URL
    '''
    # initiialize the LLM (using GTP-4o)
    llm = ChatOpenAI(
        temperature = 0, # we do not want any creative answers
        model_name = "gpt-4o",
    )

    # prompt that we want to feed in to our prompt template (includes an output indicator as a heurisitc to only output a URL)
    prompt = """Given the full name: {name_of_person}, I want you to get me a link to their LinkedIn profile page.
                    Your answer should only contain a URL"""

    prompt_template = PromptTemplate(
        template = prompt,
        input_variables = ['name_of_person'] 
    )

    # initialize the tools our search agent will be using 
    tools_for_agent = [
        Tool(
            name = "Crawl Google 4 linkedin profile page", # name our Agent refers to for this tool, is supplied to the reasoning engine
            func = get_profile_url_tavily, # the function we want the tool to run 
            description = "useful for when you need to get the LinkedIn Page URL from a first name and last name of a person" # how the LLM determines whehter to use the tool or not
        )
    ]

    # grab the react prompt - we caan provide a custom prompt in this
    react_prompt = hub.pull("hwchase17/react")

    # create our react agent 
    agent = create_react_agent(llm = llm, tools = tools_for_agent, prompt = react_prompt)

    # provide the agent the runtime by creating an agent executor that recieives an agent, tools and verbose = True so we see extensive logging 
    agent_executor = AgentExecutor(
        agent = agent, 
        tools = tools_for_agent, 
        verbose = True,
        handle_parsing_errors = True
    )

    result = agent_executor.invoke(
        input = {"input": prompt_template.format_prompt(name_of_person = name)}
    )

    # parse out the result
    linkedin_profile_url = result["output"]

    # if the result was unable to be parsed (if linkedin.com is not in the url), then return None 
    if "linkedin" not in linkedin_profile_url.lower():
        return None 
    
    return linkedin_profile_url

if __name__ == "__main__":
    linkedin_url = lookup(name = "Jasjot Parmar Data Engineer")
    print(linkedin_url)