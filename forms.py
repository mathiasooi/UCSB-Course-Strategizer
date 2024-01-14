from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired

class FiltersForm(FlaskForm):
    acronym = StringField('Acronym', validators=[DataRequired()])
