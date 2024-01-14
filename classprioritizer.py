from dag_analyze import DAGAnalyzer
import itertools
from collections import defaultdict
import csv
import re

from functools import cmp_to_key

QUARTER_NAMES = ["WINTER", "SPRING", "SUMMER", "FALL"]
class ClassPrioritizer:

    def __init__(self, dag_analyzer: DAGAnalyzer, available_courses, quarter: str):
        self.edges = defaultdict(list)
        for quarter_ind in range(4):
            if QUARTER_NAMES[quarter_ind] in quarter:
                self.quarter_ind = quarter_ind
      # self.major_courses = dag_analyzer.major_courses
        self.dag_analyzer = dag_analyzer
        self.major_reqs_set = set()
        for req in dag_analyzer.major_reqs["requirements"]:
            course_names = req["names"]
            for course in course_names:
                self.major_reqs_set.add(course)
        self.prerequisites = dag_analyzer.prerequisites
        self.available_courses_set = set(available_courses)

        for to, prereqs in self.prerequisites.items():
            self.add_edge(prereqs, to)

        self.quarters_for_course = defaultdict(set) # key=acronym, value=set containing # ids of quarters course is offered
        with open("./csvs/class.csv", newline='', encoding="utf-8") as csv_file:
            for d in csv.DictReader(csv_file):
                for q in range(4):
                    if QUARTER_NAMES[q] in d["id"]:
                        self.quarters_for_course[d["acronym"]].add(q)
    
    # this function basically creates a new DAG where the edges are reversed
    # & also not caring about the AND/OR logic present in the prereqs or concurrency data ._.
    def add_edge(self, a, to):
        if isinstance(a, str):
            if a == 'CONC':
                return
            self.edges[a].append(to)
            return
        for l in a:
            self.add_edge(l, to)

    def get_unlocked_courses(self, course):
        return self.edges[course]
    
    # Combined heuristics function used for final sorting
    #
    # May also output readable information on what determines its score; to potentially display to the user
    # (not sure if it should really be combined like that but the underlying heuristic should match up w/ what it says)
    def score(self, course: str, info_only: bool=False) -> int | str:
        helps_unlock_score = self.need_by_major_courses_for_course(course)
        quarter_delay = self.quarters_til_next_offered(course, self.quarter_ind)
        if info_only:
            may_help_unlock_ct = self.get_subtree_major_ct(course)
            return course + " may be needed to take " + str(may_help_unlock_ct) + " other courses." + ("\nIt isn't expected to be offered again for another " + str(quarter_delay) + " quarters, (" + QUARTER_NAMES[(self.quarter_ind + quarter_delay) % 4] + ")." if quarter_delay > 1 else "")
        # actual combined heuristic score
        x = helps_unlock_score * 2
        if x in itertools.chain.from_iterable([req["names"] for req in self.dag_analyzer.major_reqs["requirements"]]):
            x += quarter_delay
        return x

    def get_sorted_courses(self, courses):
        def compare(course_a: str, course_b: str):
            return self.score(course_b) - self.score(course_a)
        return sorted(courses, key=cmp_to_key(compare))
    
    def need_by_major_courses_for_course(self, prereq_course: str):
        # it's like get_subtree_major_ct but better maybe? ;)
        sum = 0
        for major_course in self.major_reqs_set:
            sum += self.course_need_for_other_course(prereq_course, major_course)
        return sum

    def course_need_for_other_course(self, prereq_course: str, goal_course: str):
        """
        Heuristic which determines how much one course needs another
        *also using the state of courses already taken

        where prereq_course is a course acronym for a possible prerequisite in the DAG for goal_course

        Return: float
        """
        if prereq_course == goal_course:
            return 1
        if goal_course not in self.prerequisites:
            return 0 # goal course had no prerequisites data, just assume it has none?
        amt = 0
        for required_options_list in self.prerequisites[goal_course]:
            if isinstance(required_options_list, str):
                print("outer prereq list had issue")
                continue
            option_present_ct = 0
            for option in required_options_list:
                if option == 'CONC':
                    continue
                found = 0
                for inner_required in option if isinstance(option, list) else [option]:
                    if inner_required == 'CONC':
                        continue
                    found = max(found, self.course_need_for_other_course(prereq_course, inner_required))
                option_present_ct += found
            amt += option_present_ct / len(required_options_list)
        return amt
            

    def get_subtree_major_ct(self, acronym: str, depth=0):
        # ignoring ors vs ands, just counting every relevant course that this course potentially unlocks
        # would be better to use something like summing course_need_for_other_course heuristic of major req courses need for this course
        c = 1 if acronym in self.major_reqs_set and acronym not in self.available_courses_set else 0
        for child in self.edges.get(acronym) or []:
            c += self.get_subtree_major_ct(child, depth+1)
        return c
    
    def quarters_til_next_offered(self, acronym: str, curr_quarter: int):
        for i in range(1, 5, 1):
            if (curr_quarter + i) % 4 in self.quarters_for_course[acronym]:
                return i
        print("this shouldn't happen! some course offered NO quarters?")
        return 0

    def num_quarters_for_course(acronym: str, taken_quarter: int, curr_quarter: int) -> int:
        # want to determine for some future course, how many quarters it would take to unlock and take that course
        # depending on when we take a prerequisite.
        # would be useful because it would help to rank whether an available REALLY needs to be taken this quarter, or can wait another
        pass



if __name__ == "__main__":
    daganalyzer = DAGAnalyzer("CMPSC", "./Majors/CMPSC/requirements.json", "keigo.json")
    # daganalyzer = DAGAnalyzer("CMPSC", "./Majors/CMPSC/requirements.json", "mathias.json")
    available_courses = daganalyzer.get_availible_courses("WINTER 2024")
    print(available_courses)
    classprioritizer = ClassPrioritizer(daganalyzer, available_courses, quarter="WINTER 2024")
    for course in ["CMPSC 24", "CMPSC 32", "CMPSC 40", "CMPSC 130A", "MATH 4B", "PSTAT 120A", "CMPSC 190A", "ECE 1A"]:
        print(course, course in available_courses)
        print(classprioritizer.get_subtree_major_ct(course), classprioritizer.need_by_major_courses_for_course(course))
        print(classprioritizer.score(course, info_only=True))
    print(classprioritizer.get_sorted_courses(available_courses))
