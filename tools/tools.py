from langchain_tavily import TavilySearchResults

def get_profile_url_tavily(name: str):
    '''
    function that takes a name as input and finds its LinkedIn or Twitter URL from Tavily 
    '''
    search = TavilySearchResults()
    res = search.run(f"{name}")
    return res