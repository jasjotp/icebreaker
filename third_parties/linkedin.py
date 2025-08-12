import os 
import requests 
from dotenv import load_dotenv 
from datetime import datetime 

load_dotenv()

# function definition that will scrape a linkedin profile 
def scrape_linkedin_profile(linkedin_profile_url: str, mock: bool = False):
    '''
    Scrapes information manually from LinkedIn profiles 

    Params: 
        linkedin_profile_url: str - URL for linkedin profile we want to scrape 
        mock: bool - Used to simulate/return dummy data from the response instead of making a real web request
    '''
    if mock: # if mock is true, get the response for the linkedin profile url from GitHub gist and return the response 
        linkedin_profile_url = "https://gist.githubusercontent.com/jasjotp/606f8e5eeebadd927cdfdf4fbcc2196c/raw/2d897f4bf093d2be5a251a3bf01496857184ea3b/jasjotparmar-scraping.json"
        response = requests.get(
            linkedin_profile_url,
            timeout = 10
        )

        # get the data is json format and return the data 
        data = response.json()
        print(f'Data returned from mock: \n{data}')
        return data
    # if mock is not true, query the scrapin io endpoint 
    else:
        api_endpoint = "https://api.scrapin.io/enrichment/profile"
        params = {
            "apikey": os.environ['SCRAPIN_API_KEY'],
            "linkedInUrl": linkedin_profile_url,
        }

        # make the reuqest to the api endpoint to get the linkedin profile above 
        response = requests.get(
            api_endpoint,
            params = params,
            timeout = 15,
        )

        # return the data we get in the response into a dictionary with the .json ethod 
        data = response.json().get('person')
        print(f'Data returned from request: {data}')

        # filter out empty fields 
        data = {
            k: v
            for k, v in data.items()
            if v not in ([], "", "", None)
        }
        return data

if __name__ == "__main__":
    print(
        scrape_linkedin_profile(linkedin_profile_url = "https://www.linkedin.com/in/jasjotparmar/", mock = True)
    )