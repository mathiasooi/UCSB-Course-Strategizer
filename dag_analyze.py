from typing import List
from collections import defaultdict
import itertools
import copy
import json
import csv
import re

from prereqParser import prereqParser

class DAGAnalyzer:
    prerequisites = dict()
    major_courses = defaultdict(list)

    def __init__(self, courses, major):
        """
        major_data sheet is json file for 
        """
        self.transcript = defaultdict(list)
        self.major = major
        
        for course in courses:
            self.transcript["courses"].append({"name": course, "passed": True})

        self.major_reqs = json.load(open(f"./Majors/{major}/requirements.json"))
        self.build_dag()

    def build_dag(self):
        """
        Build prerequisite DAG and store into static class variable
        """
        parser = prereqParser("./csvs/codenames.csv")

        with open("./csvs/course.csv", newline='', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip column description row

            for row in csv_reader:
                acronym, _, major, _, prereqs, _, _, _, _ =  row
                DAGAnalyzer.prerequisites[acronym] = parser.parseLine(prereqs)
                DAGAnalyzer.major_courses[major.split()[-1]].append(acronym)
            
    def get_availible_courses(self, quarter: str = "WINTER 2024") -> List[int]:
        """
        Find all of the major courses availible given the quarter

        Return: List of course ids
        """
        courses_passed = set(
            [
                course["name"] 
                  for course in self.transcript["courses"] 
                    if course["passed"]
            ])
        
        # print(courses_passed)

        def prereq_cleared(prereqs):
            # [[a], [b, c]] -> a must be taken, and one of b OR c must be taken
            for prereq in prereqs:
                if all(course not in courses_passed for course in prereq):
                    return False
            return True

        for _ in range(3):  # Depth 3
            for course in self.transcript["courses"]:
                # If you have taken a class and have NOT cleared the prereqs
                # We assume you have cleared them
                if course["name"] not in DAGAnalyzer.prerequisites: continue
                prereqs = DAGAnalyzer.prerequisites[course["name"]]
                if not prereq_cleared(prereqs):
                    for prereq in prereqs:
                        if len(prereq) == 1:
                            self.transcript["courses"].append({"name": prereq[0], "passed": True})
                            courses_passed.add(prereq[0])

        cleared_courses = set()

        # Add cleared major course requirements (json from major sheet) 
        for req in self.major_reqs["requirements"]:
            course_names = req["names"]
            for course in course_names:
                if course not in DAGAnalyzer.prerequisites: continue
                if not prereq_cleared(DAGAnalyzer.prerequisites[course]): continue
                cleared_courses.add(course)
        
        # Add all cleared UD major courses
        for course in DAGAnalyzer.major_courses[self.major]:
            if course not in DAGAnalyzer.prerequisites: continue
            if not prereq_cleared(DAGAnalyzer.prerequisites[course]): continue
            cleared_courses.add(course)

        offered_courses = set()  # ALL courses offered this quarter
        # Filter only for courses offered in the given quarter
        with open("./csvs/class.csv", newline='', encoding="utf-8") as csv_file:
            for d in csv.DictReader(csv_file):
                if quarter in d["id"]:
                    offered_courses.add(d["acronym"])

        availible_courses = cleared_courses.intersection(offered_courses).difference(courses_passed)

        # Filter out 
        # 1. Courses most students usually cannot take
        # 2. Courses cleared before college (implied from courses taken)
        required_courses = set(itertools.chain.from_iterable([req["names"] for req in self.major_reqs["requirements"]]))
        for course in copy.copy(availible_courses):
            num = int(re.findall(r"\d+", course)[0])
            # Skip independent/industry/research courses
            if 90 <= num <= 100 or 191 <= num <= 199:
                availible_courses.remove(course)
            # Skip LD courses that are not on major sheet
            # Courses usually not for that major
            elif num <= 100 and course not in required_courses:
                availible_courses.remove(course)
        for _ in range(3):  # Depth 3
            for course in self.transcript["courses"]:
                # If you have taken a class and have NOT cleared the prereqs
                # We assume you have cleared them
                if course["name"] not in DAGAnalyzer.prerequisites: continue
                prereqs = DAGAnalyzer.prerequisites[course["name"]]
                if not prereq_cleared(prereqs):
                    for prereq in itertools.chain.from_iterable(prereqs):
                        # Adds many duplicates, but its ok... :D
                        self.transcript["courses"].append({"name": prereq, "passed": True})
                        if prereq in availible_courses:
                            availible_courses.remove(prereq)
                
        return list(availible_courses)

if __name__ == "__main__":
    # daganalyzer = DAGAnalyzer("CMPSC", "./Majors/CMPSC/requirements.json", "keigo.json")
    # daganalyzer = DAGAnalyzer("CMPSC", "./Majors/CMPSC/requirements.json", "mathias.json")
    daganalyzer = DAGAnalyzer(["CMPSC 40", "PSTAT 120A", "CMPSC 32"], "CMPSC")
    print(daganalyzer.get_availible_courses("WINTER 2024"))
