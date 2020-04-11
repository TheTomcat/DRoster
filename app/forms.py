from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from wtforms.fields.html5 import DateField

from app.models import User, Employee, Department, Pool, Role

# class InlineButtonWidget(object):
#     html = """
#     <button type="submit" title="%s"><span>%s</span></button>
#     """

#     def __init__(self, input_type='submit'):
#         self.input_type = input_type

#     def __call__(self, field, **kwargs):
#         kwargs.setdefault('id', field.id)
#         kwargs.setdefault('type', self.input_type)
#         if 'value' not in kwargs:
#             kwargs['value'] = field._value()
#         return HTMLString(self.html % (field.name, field.lable ))

class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	remember_me = BooleanField("Remember Me")
	submit = SubmitField("Login")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EmployeeForm(FlaskForm):
    given_name = StringField('First Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    payroll_id = StringField('Payroll ID', validators=[DataRequired()])
    novel_login = StringField('Novel Username')
    pools = SelectMultipleField('Pools', coerce=int)#, choices=[])
    submit = SubmitField('Confirm')

    def set_choices(self, *, department_id):
        pools = Pool.query.filter_by(department_id=department_id).all()
        self.pools.choices = [(pool.pool_id, pool.description) for pool in pools]
    # def validate_payroll_id(self, payroll_id):
    #     employee = Employee.query.filter_by(payroll_id=payroll_id).first()
    #     if employee is not None:
    #         raise ValidationError("An employee with this payroll id already exists")

    # def validate_novel_login(self, novel_login):
    #     employee = Employee.query.filter_by(novel_login=novel_login).first()
    #     if employee is not None:
    #         raise ValidationError("An employee with this novel login already exists")

class CoverForm(FlaskForm):
	pass

class CreateRosterForm(FlaskForm):
	start = DateField("Start Date", format="%d/%M/%Y")
	end = DateField("End Date", format="%d/%M/%Y")

class CreateNewDepartment(FlaskForm):
    department_name = StringField('Department Name', validators=[DataRequired()])
    department_hr_id = StringField('Department Code', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class CreatePools(FlaskForm):
    pool_name = StringField('Pool Name', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class CreateRole(FlaskForm):
    role_name = StringField('Role Name', validators=[DataRequired()])
    pools = SelectMultipleField('Pools', coerce=int)#, choices=[])
    submit = SubmitField('Confirm')

    def set_choices(self, *, department_id):
        pools = Pool.query.filter_by(department_id=department_id).all()
        self.pools.choices = [(pool.pool_id, pool.description) for pool in pools]

class CreateRoster(FlaskForm):
    roster_start = DateField('Start Date', validators=[DataRequired()])
    roster_end = DateField('End Date', validators=[DataRequired()])
    roles = SelectMultipleField('Roles', coerce=int)
    employees = SelectMultipleField('Employees', coerce=int)
    submit = SubmitField('Confirm')
    
    def set_roles(self, *, department_id, default=None):
        roles = Role.query.filter_by(department_id=department_id).all()
        self.roles.choices = [(role.role_id, role.description) for role in roles]
        if default:
            self.roles.default = default
    
    def set_employees(self, *, department_id, default=None):
        employees = Employee.query.filter_by(department_id=department_id).all()
        self.employees.choices = [(employee.employee_id, employee.full_name) for employee in employees]
        if default:
            self.employees.default = default