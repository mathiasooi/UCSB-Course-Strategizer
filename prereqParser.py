import re
import csv

class prereqParser():
    def __init__(self, codenamesfile):
        codenames = {}
        with open(codenamesfile) as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in reader:
                codenames[row[0]] = row[1]
        self.codenames = codenames
    def clean(self,s):
        return re.sub('[\W_]+', '', s)
    def isClassNumber(self,s):
        if s == "":
            return False
        return (s[0].isdigit() or (len(s) > 1 and (s[0] == "W" or s[0] == "A") and s[1].isdigit()))
    def parseLine(self,line):
        codenames = self.codenames

        line = line.replace("Stuies","Studies")
        line = line.replace("or 5 on","")
        line = line.replace("or 3 y","")

        # Remove depercated courses
        line = line.replace("Math 4AI", "")
        line = line.replace("Math 6AI", "")
        line = line.replace("Math 3C", "")

        line = re.sub(r'W (\d)',r'W\1',line)
        line = re.sub(r'A (\d)',r'A\1',line)
        line = re.sub(r'(. or [^,]*),',r'\1 ,',line)
        line = re.sub(r'(. or [^;]*);',r'\1 ;',line)
        line = re.sub(r'(following:)([^ ])',r'\1 \2',line)
        line = re.sub(r'ITA(\d)',r'ITAL \1',line)
        line = line.replace("betaken","be taken")
        line = line.replace("may be taken conc"," CONCPREV ")
        line = line.replace("Concurrent enrollment in"," CONCNEXT ")
        line = line.replace("Concurrent with"," CONCNEXT ")

        search = re.search(r' *([^ ]*, )+[^ ]* and',line)
        if search:
            span = search.span()
            string = search.group(0)
            newStr = ""
            for i, char in enumerate(string):
                if char == ",":
                    if i + 5 <= len(string) and string[i+2:i+5] == "and":
                        continue
                    if i == 0:
                        newStr = newStr + " and"
                    elif string[i-1] == " ":
                        newStr = newStr + "and"
                    else:
                        newStr = newStr + " and"
                else:
                    newStr = newStr + char
            line = line.replace(string,newStr)

        links = []
        row = line.split(" ")
        new = []
        rawNew = []
        wait = 0
        for i in range(len(row)):
            j = 1
            while j < 3 and i + j < len(row):
                if wait == 0 and (" ".join(row[i:i+j])).upper() in codenames.values() and self.isClassNumber(self.clean(row[i+j])):
                    acro = (" ".join(row[i:i+j])).upper() + " " + self.clean(row[i+j])
                    rawAcro = (" ".join(row[i:i+j])).upper() + " " + row[i+j]
                    links.append(acro)
                    new.append([acro])
                    rawNew.append([rawAcro])
                    wait = j + 1
                    break
                j += 1
            j = 1
            while j < 7 and i + j < len(row):
                if wait == 0 and " ".join(row[i:i+j]) in codenames and self.isClassNumber(self.clean(row[i+j])):
                    # print(row[i:i+j])
                    acro = codenames[" ".join(row[i:i+j])] + " " + self.clean(row[i+j])
                    rawAcro = codenames[" ".join(row[i:i+j])] + " " + row[i+j]
                    links.append(acro)
                    new.append([acro])
                    rawNew.append([rawAcro])
                    wait = j + 1
                    break
                j += 1
            if wait == 0:
                new.append(row[i])
                rawNew.append(row[i])
            else:
                wait -= 1
        row = new
        rawRow = rawNew

        lastClass = None
        p = 0
        while p < len(row):
            if isinstance(row[p],list):
                lastClass = " ".join(row[p][0].split(" ")[:-1])
                if p == 0:
                    p = 1
                    continue
            elif lastClass != None and self.isClassNumber(row[p]) and (isinstance(row[p-1],list) or self.clean(row[p-1]).lower() == "or" or self.clean(row[p-1]).lower() == "and" or row[p-1] == "," or row[p-1] == ";"):
                rawRow[p] = [lastClass + " " + row[p]]
                row[p] = [lastClass + " " + self.clean(row[p])]
            p += 1

        if not any([isinstance(i,list) for i in row]):
            return []

        p = 0
        orgroups = []
        orgroup = []

        concNext = False
        concPrev = False
        while p < len(row):
            if row[p] == 'CONCNEXT':
                concNext = True
            if row[p] == 'CONCPREV':
                orgroups[-1].insert(0,"CONC")
            if isinstance(row[p], list):
                if p > 0 and isinstance(rawRow[p-1], list) and rawRow[p-1][0][-1] == ";":
                    # print(rawProcessed[i][p-1],orgroups)
                    if orgroup != []:
                        orgroups.append(orgroup[:])
                    orgroup = []
                if concNext:
                    orgroup.insert(0,"CONC")
                    concNext = False
                orgroup.append(row[p][0])
                p += 1
            elif self.clean(row[p]).lower() == 'or':
                if isinstance(row[p+1], list):
                    if orgroup == [] and orgroups != []:
                        orgroup = orgroups.pop()
                    orgroup.append(row[p+1][0])
                    p += 2
                else:
                    p += 1
            else:
                if orgroup != []:
                    orgroups.append(orgroup[:])
                orgroup = []
                p += 1
        if orgroup != []:
            orgroups.append(orgroup[:])

        rawDict = {re.sub(r'[^a-zA-Z0-9 ]','',r[0]):r[0] for r in rawRow if isinstance(r,list)}
        rawDict["CONC"] = "CONC"
        replace = {}
        for key in rawDict:
            if "-" in rawDict[key]:
                new = [re.sub(r'[^a-zA-Z0-9 ]','',r) for r in rawDict[key].split("-")]
                orig = new[0].split(" ")
                acro = " ".join(orig[:-1])
                number = orig[-1]
                newcourses = [acro + " " + number]
                for letter in new[1:]:
                    if len(letter) < len(number):
                        newcourses.append(acro + " " + number[:-len(letter)]+letter)
                    elif len(letter) >= len(number):
                        newcourses.append(acro + " " + letter)
                
                replace[key] = newcourses

        newOrGroups = []
        for i,group in enumerate(orgroups):
            if len(group) == 1 and "-" in rawDict[group[0]]:
                new = replace[group[0]]
                for r in new:
                    newOrGroups.append([r])
            elif len(group) > 1 and any(["-" in rawDict[group[i]] for i in range(len(group))]):
                for i,g in enumerate(group):
                    if "-" in rawDict[g]:
                        group[i] = replace[g]
                newOrGroups.append(group)
            else:
                newOrGroups.append(group)

        return newOrGroups

if __name__ == '__main__':
    parser = prereqParser()

    out = []
    with open('course.csv','r',encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            out.append(row[6])
            out.append(parser.parseLine(row[6]))
    
    with open('out.txt','w',encoding='utf-8') as f:
        for o in out:
            f.write(str(o) + "\n")