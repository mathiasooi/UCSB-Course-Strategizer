import json
import requests

class LLMInterface():
    def test(self, major, course_name, course_desc):
        url = "http://169.231.8.225:5000/v1/completions"

        headers = {
            "Content-Type": "application/json"
        }

        class LLMPrompter:
            def __init__(self, major):
                self.major = major
        course_name = "Foundations of Computer Science"
        course_desc = "Introduction to the theoretical underpinnings of computer science. Topics include propositional predicate logic, set theory, functions and relations, counting, mathematical induction and recursion (generating functions)."

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
