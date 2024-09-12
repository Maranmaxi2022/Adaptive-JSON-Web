import os
import json
import re
from flask import Flask, render_template, request
import google.generativeai as genai
from dotenv import load_dotenv

# Load the .env file containing the API key
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get the API key from the .env file
api_key = os.getenv("API_KEY")

# Configure the Gemini API
genai.configure(api_key=api_key)


# Function to load the existing data.json
def load_data():
    with open('data.json') as json_file:
        return json.load(json_file)


# Function to update the data.json file
def update_data(new_data):
    with open('data.json', 'w') as json_file:
        json.dump(new_data, json_file, indent=4)


# Function to extract JSON using regex
def extract_json(content):
    # Use regex to extract the JSON block
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return match.group(0)  # Return the matched JSON string
    else:
        raise ValueError("No valid JSON found in the content")


# Function to interact with the Gemini API and get updated content
def get_gemini_content(search_input):
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generating content based on search input
    prompt = f"Generate JSON content for a website related to {search_input}. " \
             "Provide a navbar with home, features, solutions, demo, testimonial, contact. " \
             "Also provide an intro with heading, subheading, button_text, and highlight."

    response = model.generate_content(prompt)

    # Debug: print the raw response to see what the API is returning
    print("Raw response content:")
    content = response.candidates[0].content.parts[0].text
    print(content)  # Print the response to see the actual content

    if not response.candidates:
        raise ValueError("No candidates found in the API response.")

    try:
        # Extract the valid JSON block using regex
        json_str = extract_json(content)

        print("Extracted JSON string:")
        print(json_str)  # Print the cleaned string to see what's being parsed

        # Parse the extracted JSON string
        generated_content = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON from the API response: {e}")
    except Exception as e:
        raise ValueError(f"An error occurred during JSON extraction: {e}")

    # Only update necessary fields in data.json
    default_data = load_data()

    updated_data = {
        "navbar": {
            "home": generated_content.get("navbar", {}).get("items", [])[0].get("label",
                                                                                default_data["navbar"]["home"]),
            "features": generated_content.get("navbar", {}).get("items", [])[1].get("label",
                                                                                    default_data["navbar"]["features"]),
            "solutions": generated_content.get("navbar", {}).get("items", [])[2].get("label", default_data["navbar"][
                "solutions"]),
            "demo": generated_content.get("navbar", {}).get("items", [])[3].get("label",
                                                                                default_data["navbar"]["demo"]),
            "testimonial": generated_content.get("navbar", {}).get("items", [])[4].get("label", default_data["navbar"][
                "testimonial"]),
            "contact": generated_content.get("navbar", {}).get("items", [])[5].get("label",
                                                                                   default_data["navbar"]["contact"])
        },
        "intro": {
            "heading": generated_content.get("intro", {}).get("heading", default_data["intro"]["heading"]),
            "subheading": generated_content.get("intro", {}).get("subheading", default_data["intro"]["subheading"]),
            "button_text": generated_content.get("intro", {}).get("button_text", default_data["intro"]["button_text"]),
            "highlight": generated_content.get("intro", {}).get("highlight", default_data["intro"]["highlight"])
        }
    }

    return updated_data


# Route for the home page
@app.route('/')
def index():
    json_data = load_data()
    return render_template('index.html', data=json_data)


# Route for the search page
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_input = request.form['search_input']

        try:
            # Use the search input to get updated content from the Gemini API
            updated_content = get_gemini_content(search_input)

            # Update the data.json file with the new content
            update_data(updated_content)

            return f"Updated content for: {search_input}"
        except Exception as e:
            return str(e)  # Return the error message in case of an issue

    return render_template('search.html')


if __name__ == '__main__':
    app.run(debug=True)
