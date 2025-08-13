'''
Web server that will get a POST request with the name as input and pull the ice breaker information for that person
'''
from dotenv import load_dotenv 
from flask import Flask, render_template, request, jsonify 
from ice_breaker import ice_break_with 
from werkzeug.exceptions import BadRequest

load_dotenv()

# set up a basic Flask WebServer 
app = Flask(__name__) # initiializes a new flask application

# define our index router
@app.get("/")
def index(): 
    return render_template("index.html") # render the index html template (our user interface)

# define our process route
@app.post("/process")
def process():
    try:
        my_name = request.form.get("my_name", "").strip()
        target_name = request.form.get("target_name", "").strip()
        
        if not my_name or not target_name:
            return jsonify({"error": "my_name and target_name are required"}), 400
        
        summary, profile_pic_url = ice_break_with(my_name = my_name, target_name = target_name)

        if hasattr(summary, "model_dump"):
            r = summary.model_dump()
        elif hasattr(summary, "dict"):
            r = summary.dict()
        else:
            r = {}
        
        icebreaker_msg = (
            r.get("icebreaker_message")
        )

        payload = {
            "photoUrl": profile_pic_url or "",
            "summary_and_facts": {
                "summary": r.get("summary", ""),
                "facts": r.get("facts", []),
                "common_things": r.get("common_things", []),
                "icebreaker_message": icebreaker_msg,
            },
        }

        return jsonify(payload)
    
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback 
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = True)