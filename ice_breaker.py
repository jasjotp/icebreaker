import os 
from dotenv import load_dotenv 
from typing import Tuple, Optional
from langchain_core.prompts import PromptTemplate 
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from third_parties.linkedin import scrape_linkedin_profile
from agents.linkedin_lookup_agent import lookup as linkedin_lookup_agent
from output_parsers import summary_parser, Summary
load_dotenv()

# function to extract first name from the full name 
def extract_first_name(full: str) -> str:
    return (full or "").strip().split()[0] if full else ""

def flatten_profile(profile_json: dict) -> dict:
    """
    Flattens a LinkedIn profile JSON (as returned in your example).
    Accepts either the whole API response or the `person` sub-dict.
    Purpose: To give the LLM more concise input so it hopefully outputs a valid response
    """
    # Handle both shapes: full response that contains 'person', or the person dict itself
    p = profile_json.get("person") if isinstance(profile_json, dict) and "person" in profile_json else profile_json
    if not isinstance(p, dict):
        # Return an empty but well-formed structure if we didn't get a dict
        return {
            "photoUrl": None,
            "open_to_work": False,
            "premium": False,
            "follower_count": None,
            "location": None,
            "positions_count": 0,
            "companies": [],
            "titles": [],
            "descriptions": [],
            "skills": [],
            "school_names": [],
            "degrees": [],
            "fields_of_study": [],
            "education": [],
            "languages": [],
        }

    # ---------- Education ----------
    schools_obj = p.get("schools") or {}
    edu_hist = schools_obj.get("educationHistory") or []
    school_names, degrees, fields_of_study, education_entries = [], [], [], []
    for edu in edu_hist:
        if not isinstance(edu, dict):
            continue
        school_name = edu.get("schoolName")
        degree = edu.get("degreeName")
        field = edu.get("fieldOfStudy")
        start_end = edu.get("startEndDate") or {}
        start = start_end.get("start") or {}
        end = start_end.get("end") or {}

        education_entries.append({
            "schoolName": school_name,
            "degreeName": degree,
            "fieldOfStudy": field,
            "startYear": start.get("year"),
            "startMonth": start.get("month"),
            "endYear": end.get("year"),
            "endMonth": end.get("month"),
        })

        if school_name: school_names.append(school_name)
        if degree: degrees.append(degree)
        if field: fields_of_study.append(field)

    # ---------- Positions ----------
    positions_obj = p.get("positions") or {}
    positions_data = positions_obj.get("positionHistory") or []
    companies, titles, descriptions, position_skills = [], [], [], []
    for pos in positions_data:
        if not isinstance(pos, dict):
            continue
        company = pos.get("companyName")
        title = pos.get("title")
        desc = pos.get("description") or ""

        if company: companies.append(company)
        if title: titles.append(title)
        if desc: 
            descriptions.append(desc)

            # Parse embedded skills if description contains "Skills: ..."
            # Example: "Skills: SQL Server Management Studio · Python ... , CSV"
            if "Skills:" in desc:
                skills_part = desc.split("Skills:", 1)[-1]
                # Normalize separators: turn commas into bullets, then split on bullet
                parts = skills_part.replace(",", "·").split("·")
                for s in parts:
                    skill = s.strip()
                    if skill:
                        position_skills.append(skill)

    # ---------- Skills (merge top-level + parsed from descriptions) ----------
    top_level_skills = p.get("skills") or []
    all_skills = sorted({s.strip() for s in (top_level_skills + position_skills) if s})

    # ---------- Languages -----------------------
    languages = []

    # we prefer languagesWithProficiency if present
    lw = p.get("languagesWithProficiency") or []
    if lw:
        for item in lw:
            if isinstance(item, dict):
                lang = item.get("language")
                prof = item.get("proficiency")
                if lang and prof:
                    languages.append(f"{lang} ({prof})")
                elif lang:
                    languages.append(lang)
    else:
        # fallback to plain languages list
        langs = p.get("languages") or []
        for lang in langs:
            if isinstance(lang, str):
                languages.append(lang)

    # ---------- Assemble flattened dict ----------
    flattened = {
        "photoUrl": p.get("photoUrl"),
        "open_to_work": p.get("openToWork", False),
        "premium": p.get("premium", False),
        "follower_count": p.get("followerCount"),
        "location": p.get("location"),
        "positions_count": positions_obj.get("positionsCount", 0),

        "companies": companies,
        "titles": titles,
        "descriptions": descriptions,
        "skills": all_skills,

        "school_names": school_names,
        "degrees": degrees,
        "fields_of_study": fields_of_study,
        "education": education_entries,

        "languages": languages,
    }
    print(f'Flattened profile: {flattened}')
    return flattened

# helper function on who we want to create the ice breaker for 
def ice_break_with(my_name: str, target_name: str) -> Tuple[Summary, Optional[str]]:

    my_linkedin_url = linkedin_lookup_agent(name = my_name)
    user_linkedin_url = linkedin_lookup_agent(name = target_name)

    # add the linkedin information for the user you want to find information about 
    my_linkedin_data = scrape_linkedin_profile(linkedin_profile_url = my_linkedin_url, mock = True)
    user_linkedin_data = scrape_linkedin_profile(linkedin_profile_url = user_linkedin_url)

    # get the users full name to pass into the summary prompt template 
    p = user_linkedin_data.get("person") if isinstance(user_linkedin_data, dict) and "person" in user_linkedin_data else user_linkedin_data
    
    target_full_name = " ".join(
        [str(p.get("firstName", "")).strip(), str(p.get("lastName", "")).strip()]
    ).strip() or target_name
    
    target_first_name = extract_first_name(target_full_name)

    # flatten theSS linkedin data so it is easier for the LLM to parse
    my_flattened_linkedin_data = flatten_profile(my_linkedin_data)
    user_flattened_linkedin_data = flatten_profile(user_linkedin_data)

    # declare the summary template / prompt that we pass in as a paramater to make a prompt template - information inside the curly brackets is a parameter inside the prompt template, as it is changing everytime
    summary_template = """ 
        Given a target LinkedIn profile info and my LinkedIn profile info

        Create:
        1) A short summary about the {target_full_name} (use their name; do NOT say "target person").
        2) Two interesting facts about the {target_full_name}.
        3) Identify common things between MY LinkedIn profile (JSON format): {my_profile_info} \n\n and {target_full_name} LinkedIn profile (JSON format): {target_profile_info} \n\nthat I can start a conversation about.
        \n{format_instructions}
        
        Then produce:
        4) icebreaker_message: a single paragraph I can paste into LinkedIn DM.
        - Use first person ("I").
        - Greet with "Hi {target_first_name}.
        - Mention {target_first_name} only once during the greeting.
        - Tie in 1-2 of the common things.
        - Ask one specific question that entices the target user to respond. 
        - Friendly and concise, <= 450 characters.
        - No em dashes or hyphens, totally in my tone. 
    """

    # write the placeholder of format_instructions above so LangChain can take our schema defined in the Pydantic object and plug in the schema here

    # create the prompt template from the summary template
    summary_prompt_template = PromptTemplate(
        input_variables = ['target_full_name', 'target_profile_info', 'my_profile_info', 'target_first_name'], # string that are the keys that we are going to populate with
        template = summary_template,
        partial_variables = {"format_instructions": summary_parser.get_format_instructions()}, # the schema gets plugged in at runtime - get_format_instructions takes our Pydantic object and retrieves the Pydantic schema and passes it into our format_instructions variable in our summary_template above
    )
    
    # initialize the LLM object to call the LLM to answer the prompt template
    llm = ChatOpenAI(
        temperature = 0, 
        model_name = "gpt-4o"
    )

    chain = summary_prompt_template | llm | summary_parser 
    #chain = summary_prompt_template | llm | StrOutputParser() # automatically only returns output (.content)

    res: Summary = chain.invoke(
        input = {
            "target_full_name": target_full_name,
            "target_profile_info": user_flattened_linkedin_data,
            "my_profile_info": my_flattened_linkedin_data,
            'target_first_name': target_first_name,
        }
    )

    print(res, user_flattened_linkedin_data.get("photoUrl")) # res is an AIImage object in LangChain, so use dot notation to access a certain variable like content
    return res, user_flattened_linkedin_data.get("photoUrl")

if __name__ == '__main__':
    print('Hello LangChain')
    print(os.environ.get('OPENAI_API_KEY', 'API key not found'))
    ice_break_with(my_name = "Jasjot Parmar Vancouver", target_name = "Eden Marco Google")