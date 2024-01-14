import pdfplumber
import re
import json

class Parser:
    prefixes = ['ANTH', 'ART', 'ART', 'ARTHI', 'AS', 'ASTRO', 'BIOE', 'BIOL', 'BIOL', 'BMSE', 'BL', 'CH', 'CHEM', 'CHEM', 'CH', 'CHIN', 'CLASS', 'COMM', 'C', 'CMPSC', 'CMPTG', 'CMPTGCS', 'CNCSP', 'DANCE', 'EARTH', 'EACS', 'EEMB', 'ECON', 'ED', 'ECE', 'ENGR', 'ENGL', 'ENV', 'ESS', 'ES', 'FEMST', 'FAMST', 'FR', 'GEOG', 'GER', 'GLOBL', 'GREEK', 'HEB', 'HIST', 'INT', 'INT', 'ITAL', 'JAPAN', 'KOR', 'LATIN', 'LAIS', 'LING', 'MARIN', 'MATRL', 'MATH', 'MATH', 'ME', 'MAT', 'ME', 'MES', 'MS', 'MCDB', 'MUS', 'MUS', 'MUS', 'PHIL', 'PHYS', 'PHYS', 'POL', 'PORT', 'PSY', 'RG', 'RENST', 'RUSS', 'SLAV', 'SOC', 'SPAN', 'SHS', 'PSTAT', 'TMP', 'THTR', 'W&L', 'W&L', 'WRIT']
    tolerance = 1

    def pushData(self):
        self.currClass = self.currClass.rstrip()
        self.currGrade = self.currGrade in [None,"P","A+","A","A-","B+","B","B-","C+","C"]

        self.courses.append({"name": self.currClass, "passed":self.currGrade, "units":self.page.chars[self.p]['text']})

        self.currClass = None
        self.currGrade = None

    def processLine(self):
        self.currClass = self.s
        self.currGrade = None
        self.p = self.i
        while self.p < len(self.page.chars) - 1 and self.page.chars[self.p + 1]['text'] != '.' and "bold" not in self.page.chars[self.p]['fontname'].lower():
            self.p += 1
        if "bold" in self.page.chars[self.p]['fontname'].lower():
            r = self.p + 1
            self.currGrade = self.page.chars[self.p]['text']
            if self.page.chars[self.p + 1]['text'] in ["+", "-"]:
                self.currGrade += self.page.chars[self.p + 1]['text']
                r += 1
            if not re.match(r"\d{6}", "".join([self.page.chars[k]['text'] for k in range(r,r+6)])):
                self.s = ""
                return False
        while self.p < len(self.page.chars) - 1 and self.page.chars[self.p + 1]['text'] != '.':
            self.p+=1
        return True

    def findMajor(self):
        self.major = ""
        p = self.i
        slashCount = 0
        while slashCount < 2:
            if self.page.chars[p]['text'] == '/':
                slashCount += 1
            p += 1
        spaceCount = 0
        while spaceCount < 2:
            self.major += self.page.chars[p]['text']
            if self.page.chars[p]['text'].isspace():
                spaceCount += 1
            p += 1
        self.major = self.major.strip()
    
    def parse(self, filename):
        self.startXPos = -100

        self.text = ""

        self.currClass = None
        self.currGrade = None
        self.major = None

        self.filename = "example4.pdf"

        self.courses = []

        with pdfplumber.open(filename) as pdf:
            for self.page in pdf.pages:
                self.s = ""
                self.readingName = False

                for self.i, self.c in enumerate(self.page.chars):
                    self.text += self.c['text']

                    if self.major == None and any([e in self.text for e in ["ENGR", "L&S", "CCS"]]):
                        self.findMajor()

                    if "Info" in self.text and self.startXPos == -100:
                        self.startXPos = self.page.chars[self.i + 3]['x0']

                    if self.c['x0'] > self.startXPos - self.tolerance and self.c['x0'] < self.startXPos + self.tolerance:
                        self.readingName = True

                    if self.readingName:
                        if self.c['text'] == ' ' or self.c['text'] == ':':
                            if self.s.split(' ')[0] in self.prefixes:
                                self.s += " "
                            else:
                                self.readingName = False
                                self.s = ""
                        elif self.c['text'] == '-':
                            self.readingName = False
                            if self.s.split(' ')[0] in self.prefixes:
                                if not self.processLine():
                                    continue
                                self.pushData()
                            self.s = ""
                        else:
                            self.s += self.c['text']
                    
        jsonOut = {"major": self.major, "courses": self.courses}
        return jsonOut