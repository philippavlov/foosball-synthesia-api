import oci
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

with open('config.yaml', 'r') as file:
    config_data = yaml.safe_load(file)

compartment_id = config_data['compartment_id']
CONFIG_PROFILE = config_data['config_profile']

config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

# Service endpoint
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))

@app.route('/generate', methods=['GET'])
def generate():
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_request = oci.generative_ai_inference.models.CohereChatRequest()

    # Get parameters from the GET request
    data = request.args

    print(data)


    '''
    - Goals per team: {}
        - Ball possession percentage: {}
        - Possession total (in seconds): {}
        - Match duration (in seconds): {}
        - Number of players: {}
    '''

    construct_query = """
    You are a professional football commentator. You have been invited to host a foosball tournament with round-robin matches of 3 minutes in length. There are two teams: 

    I need you to give me your best narration as if it were a live football match. Use the past tense and up to 80 words maximum.
    
    Team 1, Hornets (Yellow shirts [appears as "red" in the database]) vs Team 2: Panthers (Black shirts [appears as "blue" in the database])
    
    Here are some statistics about the match these two teams just played:

    - {}
    - {}
    - {}
    - {}
    - {}
    """.format(data['goals_per_team'],
               data['possession_percentage'],
               data['possession_total'],
               data['match_duration'],
               data['number_of_players'])


    print(construct_query)

    chat_request.message = construct_query
    chat_request.max_tokens = int(data.get('max_tokens', 300))
    chat_request.temperature = float(data.get('temperature', 1))
    chat_request.frequency_penalty = float(data.get('frequency_penalty', 0))
    chat_request.top_p = float(data.get('top_p', 0.75))
    chat_request.top_k = int(data.get('top_k', 0))

    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyawk6mgunzodenakhkuwxanvt6wo3jcpf72ln52dymk4wq")
    chat_detail.chat_request = chat_request
    chat_detail.compartment_id = compartment_id
    chat_response = generative_ai_inference_client.chat(chat_detail)
    
    data_dict = vars(chat_response)

    response_data = {
        'text': data_dict['data'].chat_response.text,
    }
    import requests

    # Post response_data to localhost:3500/synthesia
    try:
        synthesia_response = requests.post('http://localhost:3501/synthesia', json=response_data)
        synthesia_response.raise_for_status()  # Raise an exception for bad status codes
        print("Data sent successfully to Synthesia endpoint. Response:", synthesia_response.text)
    except requests.RequestException as e:
        print("Error sending data to Synthesia endpoint:", e)


    return jsonify(response_data)

if __name__ == '__main__':
    app.run(port=3500)

# llama3: ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyaycmwwnvu2gaqrffquofgmshlqzcdwpk727n4cykg34oa
# cohere.command-r-plus: ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceya7ozidbukxwtun4ocm4ngco2jukoaht5mygpgr6gq2lgq
