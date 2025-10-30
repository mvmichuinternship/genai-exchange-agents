# Change the content of the following. Look for #change this comment
import vertexai
from decider_agent.agent import root_agent
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "195472357560"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://decider-bucket"
ANALYZER_RESOURCE_ID = "5155975060502085632"
GENERATOR_RESOURCE_ID = "7810284090883571712"
ENV_VARS = {
    "ANALYZER_CARD_URL": f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}",
    "GENERATOR_CARD_URL": f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}",
}
from vertexai import agent_engines
from google.genai import types

existing_resource_name = "projects/195472357560/locations/us-central1/reasoningEngines/6185610525309665280"

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

adk_app = reasoning_engines.AdkApp(
    agent=root_agent,
)

remote_app = client.agent_engines.update(
   name=existing_resource_name,
   agent=adk_app,
   config={
        # Display name shown in the console
        "display_name": "Decider Orchestrator Agent",
        # Description for documentation
        "description": "Orchestrates various agents to make decisions based on analyzed requirements.",
        # Python dependencies needed in Agent Engine
        "requirements": open(os.path.join(os.getcwd(), "requirements.txt")).readlines() + [
            "./dist/decider-0.1.0-py3-none-any.whl"
        ],
         "extra_packages": [
            "./dist/decider-0.1.0-py3-none-any.whl",
        ],
        # Http options
        "http_options": {
            "base_url": f"https://{LOCATION}-aiplatform.googleapis.com",
            "api_version": "v1beta1",
        },
        # Staging bucket
        "staging_bucket": STAGING_BUCKET,
        "env_vars": ENV_VARS,
        "service_account": "195472357560-compute@developer.gserviceaccount.com"

    },
)

print(remote_app.resource_name)