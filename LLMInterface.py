import json
import requests
import pandas as pd

class LLMInterface():
    def getResponse(self, response):
        print(response)
        url = "http://169.231.8.225:5000/v1/completions"

        headers = {
            "Content-Type": "application/json"
        }

        major = response['major']
        course_name = self.getCourseNameFromAbrev(response['course'])
        course_desc = self.get_description_by_acronym(response['course'])

        if not course_name:
            course_name = "not provided"

        if not course_desc:
            course_desc = "not provided"

        data = {
            "max_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 20,
            "repetition_penalty": 1.15
        }


        data["prompt"] = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

        ### Instruction:
        A college student is deciding whether to take a course given the course description and name.
        Respond clearly to the student why they should take the course as soon as they can, and how it will aid them in their career.

        ### Input:


        I'm a """ + major + """ major and want to take """ + course_name + ", with the description \"" + course_desc + '"' + """ Why should I take it?

        ### Response:
        """

        import sseclient

        out = requests.post(url, headers=headers, json=data, verify=False).json()["choices"][0]["text"]

        #data['stream'] = True
        #stream_response = requests.post(url, headers=headers, json=data, verify=False, stream=True)
        #client = sseclient.SSEClient(stream_response)

        #for event in client.events():
        #    # print(event.data)
        #    payload = json.loads(event.data)
        #    print(payload['choices'][0]['text'], end='')

        i = min(out.find('\n'), out.find('#'))
        return out[0:i]
    
    def get_description_by_acronym(self, acronym, csv_file_path='csvs/class.csv'):
        # Read the CSV file into a DataFrame
        # print(csv_file_path)
        df = pd.read_csv(csv_file_path)

        # Filter rows based on the provided acronym
        selected_row = df[df['acronym'] == acronym]

        # Check if any rows match the given acronym
        if not selected_row.empty:
            # Extract and return the description
            description = selected_row['description'].values[0]
            return description
        else:
            return False

    def getCourseNameFromAbrev(self, acronym, csv_file_path='csvs/course.csv'):
        # Read the CSV file into a DataFrame
        # print(csv_file_path)
        df = pd.read_csv(csv_file_path)

        # Filter rows based on the provided acronym
        selected_row = df[df['acronym'] == acronym]

        # Check if any rows match the given acronym
        if not selected_row.empty:
            # Extract and return the description
            description = selected_row['name'].values[0]
            return description
        else:
            return False