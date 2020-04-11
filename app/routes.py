from flask import render_template, request, flash, redirect, url_for, jsonify, g
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app import app, app_name, db, auth

from app.forms import LoginForm, RegistrationForm, CreateRosterForm, EmployeeForm, CreateRoster
from app.models import Department, Role, Shift, Allocation, Employee, User, RosterVersion,get_date

import datetime as dt


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(url_for(next_page))
	return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()

	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash(f"Congratulations, you have registered for {app_name}")
		return redirect(url_for('index'))
	return render_template('register.html', title="Register", form=form)


@app.route('/<hr_id>/workforce')
def workforce(hr_id):
	department = Department.get_by_hr_id(hr_id)
	return render_template('workforce.html', department=department)

@app.route('/<hr_id>/roles')
def roles(hr_id):
	department = Department.get_by_hr_id(hr_id)
	return render_template('roles.html', department=department)

@app.route('/<hr_id>/roles/edit_form/<id>', methods=['POST'])
def edit_role(hr_id, role_id):
	department = Department.get_by_hr_id(hr_id)
	obj = request.payload


@app.route('/<hr_id>/department')
def department(hr_id):
	department = Department.get_by_hr_id(hr_id)

@app.route('/<hr_id>/roster/view/current') # View the current roster (active roster latest version)
@app.route('/<hr_id>/roster/view/id') # View a specific version of a roster
@app.route('/<hr_id>/roster/view/') # List of rosters and versions
def all_rosters(hr_id):
	department = Department.get_by_hr_id(hr_id)
	return render_template('roster_list.html', department=department)

@app.route('/<hr_id>/roster/new') # Create a roster
@app.route('/<hr_id>/roster') # Not required?
def roster_manage(hr_id):
	pass

@app.route('/<hr_id>/')
def secondary():
	@app.route('/', methods=['POST','GET'])
	def hello_world():
		form = CreateRosterForm()
		if form.validate_on_submit():
			return form.dt.data.strftime('%Y-%m-%d')
		return render_template('example.html', form=form)

	@app.route('/index')
	def index():
		user = {'username': 'Miguel'}
		return render_template('index.html', title='Home', user=user)

	@app.route('/echo', methods=['POST'])
	def echo():
		return request.json

	@app.route('/echoer')
	def echoer():
		return render_template("jstest.html")

	@app.route('/versions')
	def version():
		vers = RosterVersion.query.all()
		return render_template('version.html', versions = vers)


	@app.route('/view/<id>')
	def view(id):
		timetable = RosterVersion.query.filter_by(roster_version_id=id).first().generate_timetable()
		return render_template('view.html', data=timetable)

	@app.route('/view2/<id>')
	def view2(id):
		timetable = RosterVersion.query.filter_by(roster_version_id=id).first().generate_timetable()
		return render_template('view2.html', table=timetable)

	@app.route('/vue/<id>')
	def vue(id):
		return render_template('nav.html')

	@app.route('/<hr_id>/roles')
	def roles(hr_id):
		department = Department.get_by_hr_id(hr_id) #query.filter_by(hr_id=hr_id).first()
		# employees = department.employees
		# form = EmployeeForm(request.form)
		# department_id = department.department_id	
		# form.set_choices(department_id=department_id)
		# rendered_form = render_template('roles.html', form=form, hr_id=hr_id)
		return render_template('roles.html', department=department)#, rendered_form=rendered_form)

	@app.route('/<hr_id>/workforce')
	def workforce(hr_id):
		department = Department.get_by_hr_id(hr_id) #query.filter_by(hr_id=hr_id).first()
		# employees = department.employees
		form = EmployeeForm(request.form)
		department_id = department.department_id	
		form.set_choices(department_id=department_id)
		rendered_form = render_template('employee_create.html', form=form, hr_id=hr_id)
		return render_template('workforce.html', department=department, rendered_form=rendered_form)

	@app.route('/<hr_id>/roster/new')
	def new_roster(hr_id):
		department = Department.get(hr_id)
		form = CreateRoster(request.form)
		form.set_employees(department_id=department.department_id)
		form.set_roles(department_id=department.department_id)
		return render_template("create_roster.html", department=department, form=form)

	@app.route('/<hr_id>/modify', methods=['POST'])
	def modify(hr_id):
		if not request.method == 'POST':
			return "403"
		obj = request.json

	@app.route('/api/token')
	@auth.login_required
	def get_auth_token():
		token = g.user.generate_auth_token()
		return jsonify({ 'token': token.decode('ascii') })

	@app.route('/<hr_id>/workforce/employee/new', methods=['POST'])
	def create_employee(hr_id):
		if request.method == 'POST':
			given_name = request.form['given_name']
			surname = request.form['surname']
			payroll_id = request.form['payroll_id']
			novel_login = request.form['novel_login']
			pools = request.form['pools']
			department=Department.get_by_hr_id(hr_id)
			employee = Employee(given_name=given_name, 
								surname=surname, 
								payroll_id=payroll_id, 
								novel_login=novel_login)
			#employee.add_department(department)
			for pool_id in pools:
				employee.add_pool(pool_id = pool_id)
			db.session.add(employee)
			db.session.commit()
			return jsonify({'success': True})

		# if form.validate_on_submit():
		# 	employee = EmployeeForm(given_names=form.given_name.data, 
		# 							surname=form.surname.data,
		# 							novel_login=form.novel_login.data,
		# 							payroll_id=form.payroll_id.data)
		# 							# pools=form.pools.data)
		# 	for item in form.pools.data:
		# 		print(item)
		# return render_template('employee_create.html', form=form, department=department_id)
		
	@app.route('/vue2/<id>')
	def vue2(id):
		return render_template('nav2.html')

	@app.route('/department/<id>')
	def department(id):
		department = Department.query.filter_by(department_id=id).first()
		return render_template('department.html', department=department)

	@app.route('/role/<id>')
	def role(id):
		role = Role.query.filter_by(role_id=id).first()
		return render_template('role.html',role=role)

	@app.route('/employee/<id>')
	def employee(id):
		employee = Employee.query.filter_by(employee_id=id).first()
		print(employee)
		return render_template('employee.html',employee=employee)

	@app.route('/login', methods=['GET','POST'])
	def login():
		if current_user.is_authenticated:
			return redirect(url_for('index'))
		form = LoginForm()
		if form.validate_on_submit():
			user = User.query.filter_by(username=form.username.data).first()
			if user is None or not user.check_password(form.password.data):
				flash('Invalid username or password')
				return redirect(url_for('login'))
			login_user(user, remember=form.remember_me.data)
			next_page = request.args.get('next')
			if not next_page or url_parse(next_page).netloc != '':
				next_page = url_for('index')
			return redirect(url_for(next_page))
		return render_template('login.html', title='Sign In', form=form)


	@app.route('/logout')
	def logout():
		logout_user()
		return redirect(url_for('index'))

	@app.route('/register', methods=['GET', 'POST'])
	def register():
		if current_user.is_authenticated:
			return redirect(url_for('index'))
		form = RegistrationForm()

		if form.validate_on_submit():
			user = User(username=form.username.data, email=form.email.data)
			user.set_password(form.password.data)
			db.session.add(user)
			db.session.commit()
			flash(f"Congratulations, you have registered for {app_name}")
			return redirect(url_for('index'))
		return render_template('register.html', title="Register", form=form)

	# @app.route('/employee/list')
	# @app.route('/employee/<id>')
	# @app.route('/employee/create', methods=["GET","POST"])
	# def create_employee():
	# 	pass

	# @app.route('/user/create')
	# # Create employee account
	# @app.route()
	# #Add/remove employees to a pool
	# @app.route('/department/<department>/')
	# #Manage a department
	# @app.routes('/department/<department>/roles/add')
	# #Create roles
	# @app.routes('/department/<department>/roles/cover')
	# @app.routes('/department/<department>/roles/shift')
	# # Create shifts
	# @app.routes('/department/<department>/roster/')
	# # Manage a roster
	# @app.routes('/department/<department>/roster/generate/<start>-<end>')
	# # Create a roster
	# @app.routes('/department/<department>/roster/allocate')
	# # Allocate shifts
	# @app.routes('/leave/manage')
	# #Manage leave requests - approve/reject
			
	# @app.routes('/account/add')
	# # Create account
	# @app.routes('/account/validate/<validation>')		
	# #email validation
	# @app.routes('/account')
	# #Link to novell
	# @app.routes('/roster/view/<user|department>/<id>')
	# #View personal roster
	# #View departmental roster
	# @app.routes('/account/leave')
	# @app.routes('/account/leave/request')
	# #Request leave
	# @app.routes('/roster/swap')