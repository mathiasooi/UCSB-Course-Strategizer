import json
import requests
import pandas as pd

from collections import defaultdict
from prereqParser import prereqParser
import csv

class LLMInterface():
    def __init__(self):
        parser = prereqParser("./csvs/codenames.csv")
        prerequisites = dict()
        with open("./csvs/course.csv", newline='', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip column description row

            for row in csv_reader:
                acronym, _, major, _, prereqs, _, _, _, _ =  row
                prerequisites[acronym] = parser.parseLine(prereqs)

        self.edges = defaultdict(list)
        def add_edge(a, to):
            if isinstance(a, str):
                if a == 'CONC':
                    return
                self.edges[a].append(to)
                return
            for l in a:
                add_edge(l, to)
        for to, prereqs in prerequisites.items():
            add_edge(prereqs, to)

    def getResponse(self, response):
        url = "http://169.231.8.225:5000/v1/completions"

        headers = {
            "Content-Type": "application/json"
        }


        major = response['major']
        course_name = self.getCourseNameFromAbrev(response['course'])
        course_desc = self.get_description_by_acronym(response['course'])
        info = response['info']
        unlocks = self.edges[response['course']]

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
Respond to the input in 100 words or less

### Input:
I'm a """ + major + """ major and want to take a course with name """ + course_name + ", and with description \"" + course_desc + '"' + """. I was given the following information about this course: """ + info + """ I also know that this course is the prerequisite for """ + str(len(unlocks)) + """ other course in my major

### Response:
"""
        print(data["prompt"])


        import sseclient

        out = requests.post(url, headers=headers, json=data, verify=False).json()["choices"][0]["text"]


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

if __name__ == '__main__':
    l = LLMInterface()
    print(l.getResponse({"major":"Computer Science", "course":"MATH 4A"}))