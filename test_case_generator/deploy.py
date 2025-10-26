# Change the content of the following. Look for #change this comment
import vertexai
from testcase_agent.agent import a2a_agent
import os

PROJECT_ID = "celtic-origin-472009-n5"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://testcases-bucket"

from vertexai import agent_engines
from google.genai import types

# existing_resource_name = "projects/195472357560/locations/us-central1/reasoningEngines/5155975060502085632" #change this to your deployed agent resource name

vertexai.init(
   project=PROJECT_ID,
   location=LOCATION,
   staging_bucket=STAGING_BUCKET,
)
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{LOCATION}-aiplatform.googleapis.com/"
    ),
)

# remote_app = client.agent_engines.create(
#    #  resource_name=existing_resource_name,
#    agent_engine=root_agent,
#    display_name="Requirement Analyzer Agent",
#    requirements=open(os.path.join(os.getcwd(), "requirements.txt")).readlines()+["./dist/requirements_analyzer-0.1.0-py3-none-any.whl"],#change this to your local location
#    extra_packages=[
#        "./dist/requirements_analyzer-0.1.0-py3-none-any.whl",
#    ]
# )

remote_app = client.agent_engines.create(
#    name=existing_resource_name,
   agent=a2a_agent,
   config={
        # Display name shown in the console
        "display_name": "Test Case Generator Agent",
        # Description for documentation
        "description": "Generates test cases based on the requirements from the analyzer agent.",
        # Python dependencies needed in Agent Engine
        "requirements": open(os.path.join(os.getcwd(), "requirements.txt")).readlines() + [
            "./dist/test_case_generator-0.1.0-py3-none-any.whl"
        ],
         "extra_packages": [
            "./dist/test_case_generator-0.1.0-py3-none-any.whl",
        ],
        # Http options
        "http_options": {
            "base_url": f"https://{LOCATION}-aiplatform.googleapis.com",
            "api_version": "v1beta1",
        },
        # Staging bucket
        "staging_bucket": STAGING_BUCKET,
    },
)

print(remote_app.resource_name)