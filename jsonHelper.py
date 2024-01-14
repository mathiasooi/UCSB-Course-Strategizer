import json

class JsonHelper():
    def getCoursesFromRequirement(self, major):
        reqs = json.load(open(f"./Majors/{major}/requirements.json"))
        classes = []
        for d in reqs["requirements"]:
            classes += d["names"]
        return classes

if __name__ == '__main__':
    j = JsonHelper()
    print(j.getCoursesFromRequirement("MATH"))