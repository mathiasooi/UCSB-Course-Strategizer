import csv
from collections import defaultdict
from datetime import date
import re

class PassTimes:
    # course_acronym_to_id[course][quarter] = id
    course_acronym_to_id = defaultdict(dict)
    with open("./csvs/class.csv", encoding="utf-8") as csv_file:
        for d in csv.DictReader(csv_file):
            course_acronym_to_id[d["acronym"]][d["quarter"]] = d["id"].split()[-1]

    def __init__(self, enrollement_data: str, pass1 = date(2023, 11, 6), pass2 = date(2023, 11, 13), pass3 = date(2023, 11, 27)):
        # first_full[class] = first past time it is full
        self.first_full_data = dict()

        self.pass1 = pass1
        self.pass2 = pass2
        self.pass3 = pass3

        with open(enrollement_data) as csv_file:
            data = list(csv.DictReader(csv_file))
        for row in data:
            row["date"] = date(*[int(i) for i in re.findall(r"\d+", row["timestamp"])][:3])

        data.sort(key=lambda x: x["date"])
        for row in data:
            if row["class_id"].split()[-1] in self.first_full_data: 
                continue
            if int(row["enrolled"]) >= int(row["capacity"]):
                self.first_full_data[row["class_id"].split()[-1]] = row["date"]
    
    def first_full_pass(self, course: str, quarter: str) -> date:
        # Returns the first date when course is full
        # "open" if there are still spots after pass 3 ended
        if PassTimes.course_acronym_to_id[course][quarter] not in self.first_full_data:
            return "open"
        first_full = self.first_full_data[PassTimes.course_acronym_to_id[course][quarter]]
        if first_full <= self.pass2:
            return "pass1"
        elif self.pass2 <= first_full <= self.pass3:
            return "pass2"
        else:
            return "pass3"

if __name__ == "__main__":
    passtimes = PassTimes("./csvs/class_enrollment_1.csv")
    print(passtimes.first_full_pass("CMPSC 190I", "WINTER 2024"))
    print(passtimes.first_full_pass("CMPSC 190A", "WINTER 2024"))
    print(passtimes.first_full_pass("MATH 4A", "WINTER 2024"))
    print(passtimes.first_full_pass("MATH 117", "WINTER 2024"))
    print(passtimes.first_full_pass("CMPSC 130A", "WINTER 2024"))
    print(passtimes.first_full_pass("CMPSC 130B", "WINTER 2024"))
