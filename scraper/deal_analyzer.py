import os
import csv
import anthropic 
import serpapi
from .prompts import *

class DealAnalyzer:


    def __init__(self):
        # add anthrpic key in the environment > os.getenv("ANTHROPIC_API_KEY")
        # add serpapi key in the environment > os.getenv("SERPAPI_API_KEY")
        self.anthr_client = anthropic.Anthropic()
        self.sonnet = "claude-3-opus-20240229"
        self.serp_client = serpapi.Client(api_key=os.getenv("SERPAPI_API_KEY"))

    def get_search_result(self, query):
        results = self.serp_client.search({
            'q':query,
            'engine':"bing_shopping",
        })
        if 'organic_results' not in results:
            return "No organic results found"
        return results['organic_results']
    
    def read_csv(self, file_path):
        data = []
        with open(file_path, "r", newline="") as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                data.append(row)
        return data
    
    def save_to_csv(self, data, output_file, headers=None):
        mode = "w" if headers else "a"
        with open(output_file, mode, newline="") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            for row in csv.reader(data.splitlines()):
                writer.writerow(row)

    def understand_data_format_agent(self, sample_data):
        message = self.anthr_client.messages.create(
            model=self.sonnet,
            max_tokens=400,
            temperature=0.5,
            system=ANALYZER_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": ANALYZER_USER_PROMPT.format(sample_data=sample_data)
            }]
        )
        return message.content[0].text
    
    def analysis_agent(self, analysis_result):
        message = self.anthr_client.messages.create(
            model=self.sonnet,
            max_tokens=800,
            temperature=1,
            system=GENERATOR_SYSTEM_PROMPT,
            tools=[
                {
                    "name": "get_search_result",
                    "description": "A function that returns the search result for a given query",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string"
                            }
                        },
                        "required": ["query"],
                    },
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": analysis_result
                }
            ]
        )
        return message
    
    def calling_custom_function(self, message):
        dataFromCustomFunction = None 
        if message.stop_reason != "tool_use":
            print(".... No tool used ....")
            return dataFromCustomFunction
        if message.stop_reason == "tool_use":
            tool_params = message.content[1].input
            tool_name = message.content[1].name

        if tool_name == "get_search_result":
            result = self.get_search_result(tool_params['query'])
            if len(str(result)) > 600:
                result = str(result)[:600] + "..."
            dataFromCustomFunction = result
            print(result)
        return dataFromCustomFunction
    
    def final_response_agent(self, dataFromCustomFunction, sample_data, num_rows):
        message = self.anthr_client.messages.create(
            model=self.sonnet,
            max_tokens=1000,
            temperature=1,
            messages=[{
                "role": "user",
                "content": GENERATOR_USER_PROMPT.format(
                    num_rows=num_rows,
                    analysis_result=dataFromCustomFunction,
                    sample_data=sample_data
                )
            }]
        )
        return message.content[0].text