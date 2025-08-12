from typing import List, Dict, Any 
from langchain_core.output_parsers import PydanticOutputParser 
from pydantic import BaseModel, Field 

class Summary(BaseModel):
    summary: str = Field(description = "summary about the TARGET person")
    facts: List[str] = Field(description = "two interesting facts about them")
    common_things: List[str] = Field(
        default_factory = list, 
        description = "Up to two concrete commonalities between me and the target user"
    )
    icebreaker_message: str = Field(
        description = "A short, friendly LinkedIn message I can paste that uses the common things to spark a conversation.",
        default = ""
    )
    
    # function that recieves itself (Summary) as the object and returns the summary and facts as a dictionary  to help us serialize this object later on
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "facts": self.facts,
            "common_things": self.common_things,
            "icebreaker_message": self.icebreaker_message,
        }

# create the PydanticOutputParser 
summary_parser = PydanticOutputParser(pydantic_object = Summary)
