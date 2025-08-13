from langchain_tavily import TavilySearch

def get_profile_url_tavily(name: str):
    '''
    function that takes a name as input and finds its LinkedIn or Twitter URL from Tavily 
    '''
    search = TavilySearch()
    res = search.run(f"{name}")
    return res