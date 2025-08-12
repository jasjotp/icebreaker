'''
Web server that will get a POST request with the name as input and pull the ice breaker information for that person
'''
from dotenv import load_dotenv 
from flask import Flask, render_template, request, jsonify 
from ice_breaker import ice_break_with 

load_dotenv()

# set up a basic Flask WebServer 
app = Flask(__name__) # initiializes a new flask application

# define our index router
@app.route("/")
def index(): 
    return render_template("index.html") # render the index html template (our user interface)

# define our process route
@app.route("/process", methods = ["POST"])
def process():
    my_name = request.form.get("my_name", "").strip()
    target_name = request.form.get("target_name", "").strip()
    if not my_name or not target_name:
        return jsonify({"error": "my_name and target_name are required"}), 400
    
    summary, profile_pic_url = ice_break_with(my_name = my_name, target_name = target_name)

    if summary is None:
        return jsonify({"error": "no data returned from ice_break_with"}), 500

    return jsonify(
        {
            "summary_and_facts": summary.to_dict(), # turn the summary object to a dictionary
            "photoUrl": profile_pic_url,
        }
    )

if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = True)