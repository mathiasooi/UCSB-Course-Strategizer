from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from flask_bootstrap import Bootstrap5
from datetime import datetime
from collections import defaultdict
from transcriptPdfParser import Parser
import csv, humanize, os
from jsonHelper import JsonHelper

from pass_times import PassTimes
from dag_analyze import DAGAnalyzer
from classprioritizer import ClassPrioritizer

app = Flask(__name__)
app.secret_key = 'trdfyguhiug75r6drftyugih8767fyui6754345465dftyuvy'
Bootstrap5(app)

app.jinja_env.filters['naturaltime'] = humanize.naturaltime
app.jinja_env.filters['naturaldate'] = humanize.naturaldate

if not os.path.exists('temp'):
    os.mkdir('temp')


@app.before_request
def toggle_dark_mode():
    session.permanent = True
    if is_dark := request.args.get('is_dark'):
        session['is_dark'] = is_dark == 'True'
        return redirect(request.referrer or url_for('index'))

@app.route('/llmtest')
def llmtest():
    return render_template('llmtest.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    # files = request.files
    return render_template('courseUploadForm.html')

passtimes_per_quarter = {
    'WINTER 2024': {
        'pass2': datetime(year=2023, month=11, day=14),
        'pass3': datetime(year=2023, month=11, day=28)
    }
}

def get_enrollments(acronym: str, quarter='WINTER 2024') -> (dict, list):
    data: dict[str, list[dict]] = defaultdict(list)
    classes = []
    valid_class_ids = set()
    with open('csvs/class.csv') as file:
        for d in csv.DictReader(file):
            if d['acronym'].lower() == acronym.lower() and d['quarter'] == quarter:
                valid_class_ids.add(d['id'])
                classes.append(d)
    with open('csvs/class_enrollment_1.csv') as file:
        for d in csv.DictReader(file):
            if d['class_id'] in valid_class_ids:
                d['enrolled'] = int(d['enrolled'])
                d['capacity'] = int(d['capacity'])
                d['timestamp'] = datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                data[d['class_id']].append(d)
    return data, classes

@app.route('/enrollment', methods=['GET', 'POST'])
def enrollment():
    data: dict[str, list[dict]] = defaultdict(list)
    classes = []
    query = request.args.get('query')
    if query:
        data, classes = get_enrollments(query)
    for trends in data.values():
        trends.sort(key=lambda d: d['timestamp'])
    return render_template('enrollment.html', all_trends=data, passtimes_per_quarter=passtimes_per_quarter, classes=classes, query=query)

@app.route('/enrollment/<acronym>')
def enrollment_each(acronym: str):
    data, classes = get_enrollments(acronym)
    for trends in data.values():
        trends.sort(key=lambda d: d['timestamp'])
    return render_template('enrollment_each.html', all_trends=data, passtimes_per_quarter=passtimes_per_quarter, classes=classes, acronym=acronym)

@app.route('/handleFileUpload', methods=['POST'])
def handleFileUpload():
    f = request.files['file']
    path = os.path.join("temp", f.filename)
    f.save(path)
    jsonOut = Parser().parse(path)
    return jsonOut

@app.route('/result', methods=['GET', 'POST'])
def showResults():
    if not request.form:
        return redirect(url_for('index'))
    classes = [request.form[i] for i in request.form]
    major = classes[0]
    del classes[0]

    passtimes = PassTimes("./csvs/class_enrollment_1.csv")

    daganalyzer = DAGAnalyzer(classes, major)
    c = ClassPrioritizer(daganalyzer, daganalyzer.get_availible_courses(), "WINTER 2024")

    ranked = c.get_sorted_courses(daganalyzer.get_availible_courses())
    # ps = [passtimes.first_full_pass(course, "WINTER 2024") for course in ranked]
    # s = [(str(c.need_by_major_courses_for_course(course)), str(c.quarters_til_next_offered(course, 0))) for course in ranked]
    # classes = [[ranked[i], ps[i], s[i][0], s[i][1]] for i in range(len(ranked))]



    prosCons = []
    j = JsonHelper()
    requirements = j.getCoursesFromRequirement(major)
    for clas in ranked:
        passtime = passtimes.first_full_pass(clas, "WINTER 2024")
        unlocks = c.get_subtree_major_ct(clas)
        nextOffering = c.quarters_til_next_offered(clas, 0)

        pros = []
        neutral = []
        cons = []
        if nextOffering <= 1:
            neutral.append("This course will be offered next quarter")
        else:
            pros.append("This course will not be offered for " + str(nextOffering) + " more quarters")
        
        if unlocks == 0:
            cons.append("This course is not a prerequisite for any other course")
        elif unlocks == 1:
            neutral.append("This course is a prerequisite for one other course")
        else:
            pros.append("This course is a prerequisite for " + str(unlocks) + " other course")
        
        if clas in requirements:
            pros.append("This is a core class for your major")
        else:
            neutral.append("This is an elective class for your major")

        if passtime == 'pass1':
            pros.append("This class is popular! It's usually filled up before the end of pass 1")        
        elif passtime == 'pass2':
            pros.append("This class is popular! It's usually filled up before the end of pass 2")
        elif passtime == 'pass3':
            neutral.append("This class is usually full by the end of pass 3")
        elif passtime == 'open':
            neutral.append("This class usually has spots open by the end of pass 3")


        prosCons.append((clas, {"pros": pros, "neutral": neutral, "cons": cons}))


    return render_template('results.html', prosCons = prosCons)
    

if __name__ == '__main__':
    app.run(debug=True, port=8000)
