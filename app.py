from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from flask_bootstrap import Bootstrap5
from datetime import datetime
from collections import defaultdict, OrderedDict
from forms import FiltersForm
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

@app.before_request
def toggle_dark_mode():
    session.permanent = True
    if is_dark := request.args.get('is_dark'):
        session['is_dark'] = is_dark == 'True'
        return redirect(request.referrer or url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    # files = request.files
    return render_template('index.html')

@app.route('/enrollment', methods=['GET', 'POST'])
def enrollment():
    filters_form = FiltersForm()
    valid_class_ids = []
    data: dict[str, list[dict]] = defaultdict(list)
    classes = []
    if filters_form.validate_on_submit():
        with open('csvs/class.csv') as file:
            for d in csv.DictReader(file):
                if d['acronym'].lower() == filters_form.acronym.data.lower() and d['quarter'] == 'WINTER 2024':
                    valid_class_ids.append(d['id'])
                    classes.append(d)
        with open('csvs/class_enrollment_1.csv') as file:
            for d in csv.DictReader(file):
                if d['class_id'] in valid_class_ids:
                    d['enrolled'] = int(d['enrolled'])
                    d['capacity'] = int(d['capacity'])
                    d['timestamp'] = datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                    data[d['class_id']].append(d)
    for trends in data.values():
        trends.sort(key=lambda d: d['timestamp'])
    passtimes_per_quarter = {
        'WINTER 2024': {
            'pass2': datetime(year=2023, month=11, day=14),
            'pass3': datetime(year=2023, month=11, day=28)
        }
    }
    return render_template('enrollment.html', all_trends=data, passtimes_per_quarter=passtimes_per_quarter, classes=classes, filters_form=filters_form)

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/courseUploadForm')
def courseUploadForm():
    return render_template('courseUploadForm.html')

@app.route('/handleFileUpload', methods=['POST'])
def handleFileUpload():
    f = request.files['file']
    path = os.path.join("temp", f.filename)
    f.save(path)
    jsonOut = Parser().parse(path)
    return jsonOut

@app.route('/result', methods=['POST'])
def showResults():
    classes = [request.form[i] for i in request.form]
    major = classes[0]
    del classes[0]

    passtimes = PassTimes("./csvs/class_enrollment_1.csv")

    daganalyzer = DAGAnalyzer(classes, major)
    c = ClassPrioritizer(daganalyzer, daganalyzer.get_availible_courses(), "WINTER 2024")

    ranked = c.get_sorted_courses(daganalyzer.get_availible_courses())
    ps = [passtimes.first_full_pass(course, "WINTER 2024") for course in ranked]
    s = [(str(c.get_subtree_major_ct(course, set())), str(c.quarters_til_next_offered(course, 0))) for course in ranked]

    classes = [[ranked[i], ps[i], s[i][0], s[i][1]] for i in range(len(ranked))]

    prosCons = OrderedDict()
    j = JsonHelper()
    requirements = j.getCoursesFromRequirement(major)
    for clas, passtime, unlocks, nextOffering in classes:
        pros = []
        neutral = []
        cons = []
        if nextOffering <= 1:
            neutral.append("This course will be offered next quarter")
        else:
            pros.append("This course will not be offered for " + nextOffering + " more quarters")
        
        if unlocks == 0:
            cons.append("This course is not a prerequisite for any other course")
        elif unlocks == 1:
            neutral.append("This course is a prerequisite for one other course")
        else:
            pros.append("This course is a prerequisite for " + unlocks + " other course")
        
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


    return render_template('results.html', classes=classes)
    

if __name__ == '__main__':
    app.run(debug=True, host='169.231.155.193')
