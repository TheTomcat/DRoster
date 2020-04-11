# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, db.relationship, backref
# from sqlalchemy import Table, db.Column, db.Integer, db.String, db.ForeignKey, Smalldb.Integer, Boolean, db.DateTime, Date, Time, db.Numeric

from app import db, login, auth, app, pwd_context
import datetime as dt
from flask_login import UserMixin
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from flask import g

		
#from ical import Event
#engine = create_engine('sqlite:///test.db', echo=True)

#Base = declarative_base()

from table import Table

# class Days(object): # This should probably use an internal storage of a 7-length boolean list 
# 	_all_days = ["Monday","Tuesday","Wednesday","Thursday","Friday", "Saturday", "Sunday"]
# 	_all_codes = [2**i for i in range(0,7)]
# 	_days_of_week = {"MON":0, "TUE":1, "WED":2, "THU":3, "FRI":4, "SAT":5, "SUN":6}

# 	def __init__(self, code=None):
# 		if code is None:
# 			self.days = 0
# 		elif isinstance(code, list):
# 			if len(code) != 7:
# 				return
# 			self.code = sum([2**i * day for i, day in enumerate(code)])
	
# 	def add_days(self, day_pattern):
# 		self.code = self.code | day_pattern

# 	def remove_days(self, days):
# 		self.code = self.code & ~days

# 	def is_on_day(self, code_or_date):
# 		if isinstance(code_or_date,int):
# 			return self.code & code_or_date == code_or_date
# 		elif isinstance(code_or_date,(dt.date, dt.datetime)):
# 			return self.code & 2**code_or_date.weekday() == 2**code_or_date.weekday()

# 	@property
# 	def day_list(self):
# 		return [()]


MON = 2**0
TUE = 2**1
WED = 2**2
THU = 2**3
FRI = 2**4
SAT = 2**5
SUN = 2**6
WEEKDAY = MON + TUE + WED + THU + FRI
WEEKEND = SAT + SUN
DAYSET = [MON, TUE, WED, THU, FRI, SAT, SUN]
NAMED_DAYSET = ["Monday","Tuesday","Wednesday","Thursday","Friday", "Saturday", "Sunday"]
ABBR_DAYSET = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
ALL = WEEKEND + WEEKDAY

def on_day(test, days):
	if isinstance(days,int):
		return test & days == days
	elif isinstance(days,(dt.date, dt.datetime)):
		return test & 2**days.weekday() == 2**days.weekday()

def combine(pattern, days):
	return pattern | days

def remove(pattern, days):
	return pattern & ~days

def get_date(d):
	return dt.date(year=d.year, month=d.month, day=d.day)
def get_time(t):
	return dt.time(hour=t.hour, minute=t.minute, second=t.second)

def add_date_time(date, time):
	return dt.datetime(year=date.year,
					   month=date.month,
					   day=date.day,
					   hour=time.hour,
					   minute=time.minute,
					   second=time.second)

def daterange(start_date, end_date, include_last =False):
	offset = 1 if include_last else 0
	for n in range(int ((end_date - start_date).days + offset)):
		yield start_date + dt.timedelta(n)

def human_readable(pattern):
	output = []
	for name, day in zip(days,DAYSET):
		if on_day(pattern, day):
			output.append(name)
	return ', '.join()

def loop_over(pattern):
	for name, code in zip(NAMED_DAYSET,DAYSET):
		yield name, on_day(code, pattern)

# def create_event(Shift):
#     e = Event()
#     e.start = Shift.start
#     e.end = Shift.end
#     e.name = Shift.role.description
#     e.description = f"Shift id:{Shift.shift_id}"
#     return e


membership = db.Table("membership", #Base.metadata, 
				   db.Column("pool_id", db.Integer, db.ForeignKey("pools.pool_id")),
				   db.Column("employee_id", db.Integer, db.ForeignKey("employees.employee_id")))

rostered_roles = db.Table("rostered_roles", #Base.metadata,
				   db.Column("roster_version_id", db.Integer, db.ForeignKey("roster_versions.roster_version_id")),
				   db.Column("role_id", db.Integer, db.ForeignKey("roles.role_id")))

rostered_employees = db.Table("rostered_employee",
							db.Column("roster_version_id", db.Integer, db.ForeignKey("roster_versions.roster_version_id")),
							db.Column("employee_id", db.Integer, db.ForeignKey("employees.employee_id")))

eligibility = db.Table("eligibility",
					   db.Column("pool_id", db.Integer, db.ForeignKey("pools.pool_id")),
					   db.Column("role_id", db.Integer, db.ForeignKey("roles.role_id")))

class Department(db.Model):
	__tablename__ = "departments"
	department_id = db.Column(db.Integer, primary_key=True)
	hr_id = db.Column(db.String)
	long_name = db.Column(db.String)
	settings = db.Column(db.String)

	pools = db.relationship("Pool", back_populates="department")
	roles = db.relationship("Role", back_populates="department")
	employees = db.relationship("Employee", back_populates="department")
	roster_groups = db.relationship("RosterGroup", back_populates="department")
	leave_requests = db.relationship("LeaveRequestGroup", back_populates="department")
	colours = db.relationship("Colour", back_populates="department")

	groups = db.relationship("Group", back_populates="department")
	policies = db.relationship("Policy", back_populates="department")

	@staticmethod
	def get_by_id(department_id):
		return Department.query.filter_by(department_id=department_id).first()
	
	@staticmethod
	def get_by_hr_id(hr_id):
		return Department.query.filter_by(hr_id=hr_id).first()
	
	@staticmethod
	def get(department_or_hr_id):
		if isinstance(department_or_hr_id, Department):
			return department_or_hr_id
		else:
			return Department.get_by_hr_id(department_or_hr_id)
	
	# def __init__(self, long_name, hr_id, settings=None):
	# 	self.long_name=long_name
	# 	self.hr_id=hr_id
	# 	if settings:
	# 		self.settings=settings
		
	# 	self.generate_policies()

	def generate_policies(self):
		"""Automatically generate all policies for a newly-created department
		"""
		if self.policies:
			return None
		for function in Function.all():
			self.policies.append(Policy(department=self, function=function))
		
		# Also want to generate "admin" group who can do all of the above things
		# Ideally want to give the current user those permissions, too

	def set_admin(self, user_or_id):
		user = User.get(user_or_id)


	def get_policy(self, code_or_func):
		"""Returns a departmental policy for a given function or function code
		"""
		function = Function.get(code_or_func)
		return Policy.query.filter_by(department=self, function=function).first()

	def get_employees(self):
		output = set()
		for pool in self.pools:
			for employee in pool.employees:
				output.add(employee)
		return list(output)

	# def add_employee(self, *, employee=None, employee_id=None):
	# 	if employee_id:
	# 		employee = Employee.query.filter_by(employee_id=employee_id).first()
	# 	if employee not in self.employees:
	# 		self.employees.append(employee)

	# def remove_employee(self, *, employee=None, employee_id=None):
	# 	if employee_id:
	# 		employee = Employee.query.filter_by(employee_id=employee_id).first()
	# 	if employee in self.employees:
	# 		self.employees.remove(employee)
	# 		for pool in self.pools:
	# 			employee.remove_pool(pool)

	def add_pool(self, *, pool=None, pool_id=None):
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool not in self.pools:
			self.pools.append(pool)

	def remove_pool(self, *, pool=None, pool_id=None):
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool in self.pools:
			self.pools.remove(pool)
	
	def add_role(self, *, role=None, role_id=None):
		if role_id:
			role = Role.query.filter_by(role_id=role_id).first()
		if role not in self.roles:
			self.roles.append(role)

	def remove_role(self, *, role=None, role_id=None):
		if role_id:
			role = Role.query.filter_by(role_id=role_id).first()
		if role in self.roles:
			self.roles.remove(role)

	def __repr__(self):
		return f"Department: '{self.long_name}' ({self.hr_id})"


class Pool(db.Model):
	__tablename__ = "pools"
	pool_id = db.Column(db.Integer, primary_key=True)
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	description = db.Column(db.String)

	department = db.relationship("Department", back_populates="pools")
	roles = db.relationship("Role", secondary=eligibility, back_populates="pools")
	employees = db.relationship("Employee", secondary=membership, back_populates="pools")
	#rosters = db.relationship("Roster", back_populates="pool")
	#contracts = db.relationship("Contract", back_populates="pools")

	@staticmethod
	def get(pool_id):
		if isinstance(pool_id, Pool):
			return pool_id
		return Pool.query.filter_by(pool_id=pool_id).first()

	def __repr__(self):
		return f"Pool: {self.department}->{self.description} ({str(len(self.employees))})"

class Role(db.Model):
	__tablename__ = "roles"
	role_id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.String)
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	#pool_id = db.Column(db.Integer, db.ForeignKey("pools.pool_id"))

	department = db.relationship("Department", back_populates="roles")
	pools = db.relationship("Pool", secondary=eligibility, back_populates="roles")
	shifts = db.relationship("Shift", back_populates="role")
	covers = db.relationship("DefaultCover", back_populates="role")
	roster_versions = db.relationship("RosterVersion", secondary=rostered_roles, back_populates="roles")

	@staticmethod
	def get(role_or_id):
		if isinstance(role_or_id, Role):
			return role_or_id
		return Role.query.filter_by(role_id=role_or_id).first()

	def remove_pool(self, *, pool_id=None, pool=None):
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool in self.pools:
			self.pools.remove(pool)

	def add_pool(self, *, pool_id=None, pool=None):
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool not in self.pools:
			self.pools.append(pool)

	def __repr__(self):
		return f"Role: '{self.department.hr_id}'->'{self.description}'"
# class Membership(db.Model):
# 	__tablename__ = "membership"
# 	membership_id = db.Column(db.Integer, primary_key=True)
# 	employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
# 	pool_id = db.Column(db.Integer, db.ForeignKey("pools.pool_id"))

class Employee(db.Model):
	__tablename__ = "employees"
	employee_id = db.Column(db.Integer, primary_key=True)
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	novel_login = db.Column(db.String)
	payroll_id = db.Column(db.String)
	given_name = db.Column(db.String)
	preferred_name = db.Column(db.String)
	surname = db.Column(db.String)
	user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
	start_date = db.Column(db.Date)
	end_date = db.Column(db.Date)
	
	department = db.relationship("Department", back_populates="employees")
	pools = db.relationship("Pool", secondary=membership, back_populates="employees")
	roster_versions = db.relationship("RosterVersion", secondary=rostered_employees, back_populates="employees")
	allocations = db.relationship("Allocation", back_populates="employee")
	leave_requests = db.relationship("LeaveRequestGroup", back_populates="employee")
	user = db.relationship("User", back_populates="employees")

	def add_pool(self, *, pool=None, pool_id=None):
		#print(f"pool_id:{pool_id} Pool:{pool}")
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool not in self.pools:
			self.pools.append(pool)
			self.add_department(department=pool.department)

	def remove_pool(self, *, pool=None, pool_id=None):
		if pool_id:
			pool = Pool.query.filter_by(pool_id=pool_id).first()
		if pool in self.pools:
			self.pools.remove(pool)
	
	@staticmethod
	def get(employee_or_id):
		if isinstance(employee_or_id, Employee):
			return Employee
		return Employee.query.filter_by(employee_id=employee_or_id)

	@property
	def full_name(self):
		return self.given_name + " " + self.surname

	@property
	def all_data(self):
		return ''.join([self.given_name,self.surname, self.payroll_id, self.novel_login])

	def __repr__(self):
		return f"Employee: {self.given_name} {self.surname} ({self.payroll_id})"

class Shift(db.Model):
	__tablename__ = "shifts"
	shift_id = db.Column(db.Integer, primary_key=True)
	role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"))
	start = db.Column(db.DateTime)
	end = db.Column(db.DateTime)
	rostered_hours = db.Column(db.Numeric)
	overtime_hours = db.Column(db.Numeric)
	is_required = db.Column(db.Boolean, default=True)
	allow_overload = db.Column(db.Boolean, default=False)

	role = db.relationship("Role", back_populates="shifts")
	allocations = db.relationship("Allocation", back_populates="shift")

	@staticmethod
	def get(shift_or_id):
		if isinstance(shift_or_id, Shift):
			return shift_or_id
		return Shift.query.filter_by(shift_id=shift_or_id).first()

	def overlaps(self, other):
		return self.end > other.start & self.start < other.end

	def __repr__(self):
		return f"Shift: {self.role.description} - ({self.start.strftime('%d/%m/%Y %H:%m %p')})"

class Allocation(db.Model):
	__tablename__ = "allocations"
	allocation_id = db.Column(db.Integer, primary_key=True)
	shift_id = db.Column(db.Integer, db.ForeignKey("shifts.shift_id"))
	employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))

	roster_version_id = db.Column(db.Integer, db.ForeignKey("roster_versions.roster_version_id"))
	timestamp = db.Column(db.DateTime)
	is_variation = db.Column(db.Boolean)

	shift = db.relationship("Shift", back_populates="allocations") 
	employee = db.relationship("Employee", back_populates="allocations")
	roster_version = db.relationship("RosterVersion", back_populates="allocations")

	@staticmethod
	def get(allocation_or_id):
		if isinstance(allocation_or_id, Allocation):
			return allocation_or_id
		return Allocation.query.filter_by(allocation_id=allocation_or_id).first()

	def swap(self, other):
		self.employee, other.employee = other.employee, self.employee
		self.is_variation = True
		other.is_variation = True

	def clone(self, roster_version):
		new = Allocation(shift = self.shift,
						 employee = self.employee,
						 roster_version = roster_version)
		return new

class DefaultCover(db.Model):
	__tablename__ = "defaultcovers"
	cover_id = db.Column(db.Integer, primary_key=True)
	role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"))
	description = db.Column(db.String)
	start = db.Column(db.Time)
	end = db.Column(db.Time)
	days = db.Column(db.Integer)
	# overnight = db.Column(Boolean)
	rostered_hours = db.Column(db.Numeric)
	overtime_hours = db.Column(db.Numeric)
	fore_colour = db.Column(db.String)
	back_colour = db.Column(db.String)
	is_required = db.Column(db.Boolean, default=True)
	allow_overload = db.Column(db.Boolean, default=False)

	role = db.relationship("Role", back_populates="covers")
	
	def readable_days(self):
		return human_readable(self.days)

	def get_day_list(self):
		output = []
		for name, code in zip(NAMED_DAYSET,DAYSET):
			output.append((name, on_day(self.days, code)))
		return output

	def create_shifts(self, start=None, days=7):
		d_offset = 0 if self.start < self.end else 1
		if start is None: # do this week for 7 days
			start = dt.now().date()
			start = get_date(start) - dt.timedelta(days=start.weekday())  		
		output = []
		for day in range(days):
			d_start = start + dt.timedelta(days=day)
			d_end = start + dt.timedelta(days=day+d_offset)
			if on_day(self.days, d_start):
				output.append(Shift(start=add_date_time(d_start,self.start),
									end=add_date_time(d_end, self.end),
									rostered_hours=self.rostered_hours,
									overtime_hours=self.overtime_hours,
									role=self.role))
		return output

class RosterGroup(db.Model):
	__tablename__ = "roster_groups"
	roster_group_id = db.Column(db.Integer, primary_key=True)
	department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
	description = db.Column(db.String)

	department = db.relationship("Department", back_populates="roster_groups")
	rosters = db.relationship("Roster", back_populates="roster_group")

class Roster(db.Model):
	__tablename__ = "rosters"
	roster_id = db.Column(db.Integer, primary_key=True)
	roster_group_id = db.Column(db.Integer, db.ForeignKey('roster_groups.roster_group_id'))

	start = db.Column(db.Date)
	end = db.Column(db.Date)
	manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

	last_version_id = db.Column(db.Integer, db.ForeignKey('roster_versions.roster_version_id'))
	#department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))

	#department = db.relationship("Department", back_populates="rosters")
	manager = db.relationship("User", back_populates="manages")
	roster_group = db.relationship("RosterGroup", back_populates="rosters")
	roster_versions = db.relationship("RosterVersion", back_populates="roster", foreign_keys="RosterVersion.roster_id")
	last_version = db.relationship("RosterVersion", foreign_keys=[last_version_id])

	@property
	def most_recent_version(self):
		return roster_versions[-1]

	###### THESE SHOULD ALL BE IN ROSTERVERSIONS

	def add_employee(self, employee):
		if not self.is_employee(employee):
			self.employees.append(employee)
	def remove_employee(self, employee):
		if self.is_employee(employee):
			self.employees.remove(employee)
	def is_employee(self, employee):
		return employee in self.employees

	def add_role(self, role):
		if not self.is_role(role):
			self.roles.append(role)
	def remove_role(self, role):
		if self.is_role(role):
			self.roles.remove(role)
	def is_role(self, role):
		return role in self.roles

	def create_new_version(self, base=None, version_number=None):
		if version_number is None:
			version_number = RosterVersion.query.filter_by(roster=self).order_by(RosterVersion.version_number.desc).last().version_number + 1
		elif RosterVersion.query.filter_by(roster=self).filter_by(version_number=version_number):
			raise ValueError()
		new_version = RosterVersion(roster = self,
									version_number = version_number,
									state="draft")	
		if base is None:
			for employee in self.employees:
				pass
			# Get list of roles
			# iterate over date range
			# Create shifts as per cover
			# Don't allocate employees
			pass
		elif isinstance(base, RosterVersion):
			
			for allocation in base.allocations:
				allocation.clone(new_version)
			# Duplicate the allocations, but link to new roster_version
			return new_version
		else:
			pass

class RosterVersion(db.Model):
	__tablename__ = "roster_versions"
	roster_version_id = db.Column(db.Integer, primary_key=True)
	roster_id = db.Column(db.Integer, db.ForeignKey("rosters.roster_id"))
	version_number = db.Column(db.Integer)
	state = db.Column(db.String)
	is_first = db.Column(db.Boolean)

	roster = db.relationship("Roster", back_populates="roster_versions", foreign_keys=[roster_id])
	allocations = db.relationship("Allocation", back_populates="roster_version")

	employees = db.relationship("Employee", secondary=rostered_employees, back_populates="roster_versions")#, lazy='dynamic')
	roles = db.relationship("Role", secondary=rostered_roles, back_populates="roster_versions")

	def allocate(self, employee_or_id, shift_or_id):
		# Check that this shift is in this roster
		# Find the allocation 
		# Check that there is no existing allocation, or that overload is allowed
		shift = Shift.get(shift_or_id)
		if shift.role not in self.roster.roles:
			return None
		
		allocations = Allocation.query.filter_by(roster_version=self, shift=shift).all()

		employee = Employee.get(employee_or_id)

	def manager(self):
		return self.roster.manager		

	def employee_list(self, key=None):
		if key is None:
			key = lambda x: x.surname
		emplist = set()
		first = get_date(self.allocations[0].shift.start)
		last = get_date(self.allocations[0].shift.start)
		for allocation in self.allocations:
			emplist.add(allocation.employee)
			this = get_date(allocation.shift.start)
			if first > this:
				first = this
			if last < this:
				last = this
		# print(first, last)
		emplist = list(emplist)
		emplist.sort(key=key)
		return emplist 

	def date_range(self):
		self.allocations.sort(key=lambda x: x.shift.start)
		first = get_date(self.allocations[0].shift.start)
		last = get_date(self.allocations[-1].shift.start) 
		return first, last

	def generate_timetable(self):
		T = Table(has_header_column = True, has_header_row = True)

		emplist = self.employee_list()
		top_row = [e.given_name + " " + e.surname for e in emplist]
		#top_row_metadata = [f'id={e.employee_id}' for e in emplist]

		first, last = self.date_range()
		date_list = [r for r in daterange(first,last, include_last=True)]
		first_col = [date.strftime("%d/%m/%Y") for date in date_list]#r in daterange(first,last, include_last=True)]
		row_metadata = [{"class":[NAMED_DAYSET[date.weekday()]]} for date in date_list] #r in daterange(first, last, include_last=True)]
		# print(row_metadata)
		T.initialise_by_headers(column_headers=top_row, row_headers=first_col)
		#T.add_table_metadata(metadata={'border':["1"], "class":["table","table-bordered","table-hover"]})
		# T.add_header_row_metadata({""})
		#T.add_top_row_metadata(metadata=top_row_metadata)
		[T.add_row_metadata(row_index=i, metadata=metadata) for i, metadata in enumerate(row_metadata)]
		for allocation in self.allocations:
			T.insert_into(row_header=get_date(allocation.shift.start).strftime("%d/%m/%Y"),
						  col_header=allocation.employee.full_name, 
						  value=allocation.shift.role.description)#,
						#   metadata={"id":[f"alloc{allocation.allocation_id}"]})
		
		return T.build_html_table()

class Swap(db.Model):
	__tablename__ = "swaps"
	swap_id =  db.Column(db.Integer, primary_key=True)
	allocation_id = db.Column(db.Integer, db.ForeignKey("allocations.allocation.id"))
	employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
	approval_a = db.Column(db.Integer, db.ForeignKey("approvals.approval_id"))
	approval_b = db.Column(db.Integer, db.ForeignKey("approvals.approval_id"))
	
class LeaveRequestGroup(db.Model):
	__tablename__ = "leave_request_groups"
	leave_request_group_id = db.Column(db.Integer, primary_key=True)
	employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	date_submitted = db.Column(db.DateTime)
	description = db.Column(db.String)

	employee = db.relationship("Employee", back_populates="leave_requests")
	leave = db.relationship("Leave", back_populates="request_group")
	department = db.relationship("Department", back_populates="leave_requests")

class Leave(db.Model):
	__tablename__ = "leave"
	leave_id = db.Column(db.Integer, primary_key=True)
	request_group_id = db.Column(db.Integer, db.ForeignKey("leave_request_groups.leave_request_group_id"))
	date = db.Column(db.Date)
	approval_id = db.Column(db.Integer, db.ForeignKey("approvals.approval_id"))

	approval = db.relationship("Approval", uselist=False)
	request_group = db.relationship("LeaveRequestGroup", back_populates="leave")

	@property
	def is_approved(self):
		return approval.approved

	@property
	def approved_on(self):
		return approval.timestamp

	@property
	def approved_by(self):
		return approval.approved_by

	def approve(self, user_or_id, timestamp=None):
		user = User.get(user_or_id)
		if timestamp is None:
			timestamp = dt.datetime.now()
		a = Approval(approved_by = user, timestamp=timestamp, approved = True)
		self.approval = a

class Approval(db.Model):
	__tablename__ = "approvals"
	approval_id = db.Column(db.Integer, primary_key=True)
	is_reviewed = db.Column(db.Boolean, default=False)
	is_approved = db.Column(db.Boolean, default=None)
	approved_by_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
	timestamp = db.Column(db.DateTime)
	
	approved_by = db.relationship("User", back_populates="approvals")

class Colour(db.Model):
	__tablename__ = "colours"
	colour_id = db.Column(db.Integer, primary_key=True)
	r = db.Column(db.Integer)
	g = db.Column(db.Integer)
	b = db.Column(db.Integer)
	description = db.Column(db.String)

	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	department = db.relationship("Department", back_populates="colours")

	def darken(self):
		c = Colour(description=f"{self.description}-dark")
		shade = 0.1
		d = lambda x: int(x * (1 - shade))
		(c.r, c.g, c.b) = map(d, (self.r, self.g, self.b)) 
		return c

	def lighten(self):
		c = Colour(description=f"{self.description}-light")
		tint = 0.1
		d = lambda x: int(x + (255-x) * tint)
		(c.r, c.g, c.b) = map(d, (self.r, self.g, self.b)) 
		return c

	@property
	def hex(self):
		return f"#{((self.r << 16) + (self.g << 8) + self.b):X}"

	@staticmethod
	def hexstr_to_rgb(hexstr):
		RGB = int(hexstr.strip("#"), 16)
		return Colour.hex_to_rgb(RGB)
	
	@staticmethod
	def hex_to_rgb(RGB):
		R = RGB >> 16
		G = (RGB & 0x00ff00) >> 8
		B = RGB & 0x0000ff
		return (R,G,B)

	@staticmethod
	def new_colour():
		pass #Some sort of generator to automatically 
		# Create new colours (probably from just a predefined list)
		# - pastel, neon, https://mokole.com/palette.html

	def set_fromhex(self, hexstr):
		self.r, self.g, self.b = Colour.hexstr_to_rgb(hexstr)
		
	def __repr__(self):
		return f"Colour({self.hex}, {self.description})"

group_policies = db.Table("group_policies",
					   db.Column("group_id", db.Integer, db.ForeignKey("groups.group_id")),
					   db.Column("policy_id", db.Integer, db.ForeignKey("policies.policy_id")))

user_group = db.Table("user_group",
					  db.Column("user_id", db.Integer, db.ForeignKey("users.user_id")),
					  db.Column("group_id", db.Integer, db.ForeignKey("groups.group_id")))

class Group(db.Model):
	__tablename__ = "groups"
	group_id = db.Column(db.Integer, primary_key=True)
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	name = db.Column(db.String)

	policies = db.relationship("Policy", secondary=group_policies, back_populates="groups")
	department = db.relationship("Department", back_populates="groups")
	users = db.relationship("User", secondary=user_group, back_populates="groups")

	def grant(self, function_or_code):
		# Get the policy
		policy = Policy.get(self.department, function_or_code) # self.department.get_policy(function_or_code)
		if policy not in self.policies:
			self.policies.append(policy)
	
	def revoke(self, function_or_code):
		policy = Policy.get(self.department, function_or_code) #self.department.get_policy(function_or_code)
		if policy in self.policies:
			self.policies.remove(policy)		

	def __repr__(self):
		return f"Group <{self.department.hr_id}:{self.name} policies={[i.function.code for i in self.policies]}"

class Policy(db.Model): # THIS SHOULD BE CALLED PERMISSIONS
	__tablename__ = "policies"
	policy_id = db.Column(db.Integer, primary_key=True)
	department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
	function_id = db.Column(db.Integer, db.ForeignKey("functions.function_id"))

	groups = db.relationship("Group", secondary=group_policies, back_populates="policies")
	department = db.relationship("Department", back_populates="policies")
	function = db.relationship("Function", back_populates="policies")

	def __repr__(self):
		return f"Policy <{self.department.hr_id}:{self.function.code}> ({self.function.name})"

	@property
	def policy_code(self):
		return f"{self.department.hr_id}:{self.function.code}"
	
	@property
	def dept(self):
		return f"{self.department.hr_id}"

	# @property
	# def func

	@staticmethod
	def get(department_or_hr_id, function_or_code):
		department = Department.get(department_or_hr_id)
		function = Function.get(function_or_code)
		return Policy.query.filter_by(department=department, function=function).first()

class Function(db.Model):  #THIS SHOULD BE CALLED ACTIONS
	__tablename__ = "functions"
	function_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	code = db.Column(db.String)

	policies = db.relationship("Policy", back_populates="function")

	@staticmethod
	def all():
		for function in Function.query.all():
			if function.code != "su":
				yield function

	@staticmethod
	def get_superuser_function():
		return Function.query.filter_by(code="su").first()

	@staticmethod
	def get(function_or_code):
		print(f"Getting function: {function_or_code}")
		if isinstance(function_or_code, Function):
			return function_or_code
		else:
			return Function.query.filter_by(code=function_or_code).first()

def _generate_functions():
	# List of functions
	funcs = []
	
	funcs.append(Function(name="Superuser", code="su"))

	funcs.append(Function(name="View Current Roster", code="view_roster_current"))
	funcs.append(Function(name="View Old Roster", code="view_roster_old"))
	funcs.append(Function(name="Create New Roster", code="create_roster"))
	funcs.append(Function(name="Modify Current Roster", code="modify_roster"))
	funcs.append(Function(name="Publish Roster", code="publish_roster"))

	funcs.append(Function(name="Request Shift Swap", code="request_swap"))
	funcs.append(Function(name="Approve Shift Swap", code="approve_swap"))
	funcs.append(Function(name="Request Leave", code="request_leave"))
	funcs.append(Function(name="Approve Leave", code="approve_leave"))

	funcs.append(Function(name="Manage Department", code="manage_department"))

	db.session.add_all(funcs)
	db.session.commit()

def _create_superuser():
	superuser_function = Function.get_superuser_function()
	superuser_policy = Policy(function=superuser_function)
	superuser_group = Group(name="superusers")
	superuser_group.grant(superuser_function)
	U = User(username="root", email="")
	U.add_to_group(superuser_group)
	U.set_password("default")

	assert U.has_permission(superuser_policy)

class User(UserMixin, db.Model):
	__tablename__ = "users"
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20))
	password_hash = db.Column(db.String(100))
	email = db.Column(db.String(100))
	mobile = db.Column(db.String(20))
	last_seen = db.Column(db.DateTime)
	is_active = db.Column(db.Boolean, default=False)
	session_token = db.Column(db.String, unique=True)
	
	approvals = db.relationship("Approval", back_populates="approved_by")
	employees = db.relationship("Employee", back_populates="user")
	groups = db.relationship("Group", secondary=user_group, back_populates="users")
	manages = db.relationship("Roster", back_populates="manager")

	def set_session_token(self):
		s = Serializer(app.config['SECRET_KEY'])
		# s.dumps

	def seen(self):
		self.last_seen = dt.datetime.now()

	def longprint(self):
		output = ""
		output += f"User: {self.username}:{self.password_hash} {('(active)' if self.is_active else '')}\n"
		output += f"      e:{self.email}, m:{self.mobile}\n"
		output += f"      last seen: {self.last_seen}\n"
		output += f"\n"
		output += f"      Claimed employees: {', '.join(map(lambda x: x.full_name, self.employees))}\n"
		output += f"      Groups: {', '.join(map(lambda x: x.name, self.groups))}"
		return output

	def has_permission(self, policy):
		# Does the user have explicit permission
		for group in self.groups:
			if policy in group.policies:
				return True
		# Is the user a superuser
		su = Function.get_superuser_function()
		for group in self.groups:
			for policy in groups.policies:
				if policy.function is su:
					return True
		return False

	def claim_employee(self, employee_or_id):
		employee = Employee.get(employee_or_id)
		self.employees.append(employee)

	def add_to_group(self, group):
		# group = Group.get_by(group)
		if group not in self.groups:
			self.groups.append(group)
	
	def remove_from_group(self,group):
		# group = Group.get_by(group)
		if group in self.groups:
			self.groups.remove(group)

	@staticmethod
	def get(user_or_id):
		if isinstance(user_or_id, User):
			return user_or_id
		return User.query.filter_by(user_id=user_or_id).first()

	@property
	def get_id(self):
		return self.session_token
	
	@property
	def is_anonymous(self):
		return False

	def set_password(self, password):
		self.password_hash = pwd_context.hash(password)
	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)
	@staticmethod
	def hash_password(password):
		return pwd_context.hash(password)

	def generate_auth_token(self, expiration=600):
		s = Serializer(app.config['SECRET_KEY'],
					   expires_in=expiration)
		return s.dumps({'id':self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except SignatureExpired:
			return None #Valid token, but expired
		except BadSignature:
			return None #Invalid token
		user = User.query.get(data['id'])
		return user

@login.user_loader
def load_user(session_token):
	return User.query.filter_by(session_token=session_token)#get(int(id))

@auth.verify_password
def verify_password(username_or_token, password):
	user = User.verify_auth_token(username_or_token)
	if not user:
		user = User.query.filter_by(username=username_or_token).first()
		if not user or not user.verify_password(password):
			return False
	g.user = user
	return True


def generate_filler():
	_generate_functions()
	_create_superuser()

	users = [User(username=f"user{i}", password_hash=User.hash_password(f"user{i}")) for i in range(1,4)]

	from random import choice, randint
	ICU = Department(long_name="Royal Brisbane and Women's Hospital Department of Intensive Care Medicine", 
					 hr_id="rbwhicu")
	
	ICU.generate_policies()

	JR_pool = Pool(description="ICU JR Pool", department=ICU)

	SR_pool = Pool(description="ICU SR Pool", department=ICU)
	Con_pool = Pool(description="ICU Consultant Pool", department=ICU)

	role_names = ["Pod 1 (HDU)", "Pod 2 JR", "Pod 3 JR", "Pod 4 JR", "MERT"]

	SR_role_names = ["Pod 2 SR", "Pod 3 SR", "Pod 4 SR", "Long", "Night SR"]

	Roles = []
	for name in role_names:
		r = Role(description=name, department=ICU)
		r.add_pool(pool=JR_pool)
		Roles.append(r)
	for name in SR_role_names:
		r = Role(description=name, department=ICU)
		r.add_pool(pool=SR_pool)
		Roles.append(r)

	employee_names = [("Oscar", "Close"),
					  ("Joe","Passantino"),
					  ("Jessica","Byrne"),
					  ("Bec","King"),
					  ("Tom","Vos"),
					  ("Denver","Khoo"),
					  ("Bianca", "Rajapaske"),
					  ("Liz","Hallt"),
					  ("Matt","Bright"),
					  ("Nisha","Singh"),
					  ("Branco", "Wu"),
					  ("Nicole", "Jacobs"),
					  ("Luke", "Carr"),
					  ("David","Sidhom"),
					  ("Tommy","Lam"),
					  ("Hannah","Woodcock"),
					  ("Mitchell","Cox"),
					  ("Anthony","Deacon"),
					  ("Jamie","Reynolds"),
					  ("Kate","Taylor")]
	Employees = []
	rg = RosterGroup(department=ICU, description="JR Roster")
	roster = Roster(roster_group=rg, start=get_date(dt.datetime.now()),
					end = get_date(dt.datetime.now() + dt.timedelta(days=14)))
	
	ver = RosterVersion(roster=roster, version_number=1, state="draft")
	ver2 = RosterVersion(roster=roster, version_number=2, state="draft")
	for version in [ver, ver2]:
		for role in JR_pool.roles:
			version.roles.append(role)
		for i,(first, sur) in enumerate(employee_names):
			e = Employee(given_name = first, surname=sur, payroll_id=f"{i}", novel_login=sur[:6]+first[:3], 
				pools=[JR_pool], department=ICU, start_date = dt.datetime.now())
			Employees.append(e)
			version.employees.append(e)

	# roster = Roster(pool=JR_pool)

	mane = dt.time(hour=7,minute=30)
	hleven=dt.time(hour=11,minute=30)
	mane1 = dt.time(hour=8)
	nocte = dt.time(hour=19,minute=30)
	nocte1=dt.time(hour=20)
	nocte2 = dt.time(hour=20,minute=30)
	dc = [([Roles[0]],mane,nocte1,WEEKDAY,False, 12, 0), # 1 D
		  ([Roles[0]],mane,hleven,SAT,False,4,0), #1 Sat
		  (Roles[1:4],mane,nocte1,ALL,False, 12, 0), # 2-4D
		  ([Roles[0]],nocte,mane1,WEEKDAY,True, 12, 0), #1 N
		  (Roles[1:4],nocte,mane1,ALL,True,12,0),#2-4N
		  ([Roles[4]],mane1,nocte2,WEEKDAY,False, 12,0)] # MERT
	DC=[]
	# print()
	for (roles, start, end, days, overnight, rost, over) in dc:
		# print(roles)
		for role in roles:
			C = DefaultCover(start=start, end=end, days=days, #overnight=overnight,
			rostered_hours=rost, overtime_hours=over, role=role)
			DC.append(C)

		# cover_id = db.Column(db.Integer, primary_key=True)
		# role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"))
		# start = db.Column(db.Time)
		# end = db.Column(db.Time)
		# days = db.Column(db.Integer)
		# overnight = db.Column(Boolean)
		# rostered_hours = db.Column(db.Numeric)
		# overtime_hours = db.Column(db.Numeric)
	Shifts = []
	for cover in DC:
		print(f"Creating cover for {cover.role.description}")
		Shifts += cover.create_shifts(start=dt.date(2020,3,9),days=14)

	# random allocations
	alloc = []
	for version in [ver,ver2]:
		for shift in Shifts:
			t = dt.datetime.now()
			a = Allocation(shift=shift,
						   roster_version=version,
						   employee=choice(Employees),
						   timestamp=t)

	# Session = sessionmaker(bind=engine)
	# session = Session()
	leaves = []
	requests = []
	for i in range(0,10):
		LRG = LeaveRequestGroup(employee=choice(Employees),
								date_submitted=dt.datetime.now(),
								description=f"LRG{i}")
		start_date = dt.date(2020,3,9) + dt.timedelta(days=randint(1,9))
		for i in range(0,choice([2,3,4,5,6])):
			L = Leave(request_group=LRG,
					 date=start_date+dt.timedelta(days=i))
			leaves.append(L)
		requests.append(LRG)

	# P = []
	# for func in Function.all():
	# 	P.append(Policy(function=func, department=ICU))
	ICU.generate_policies()

	#Make some colours

	C = {"slate-grey":0x2f4f4f, "forest-green":0x228b22,
	"orangered":0xff4500, "slate-blue":0x6a5acd,
	"yellow": 0xffff00, "lime": 0x00ff00,
	"aqua":0x00ffff,"blue":0x0000ff,
	"deep-pink":0xff1493, "moccasin":0xffe4b5}
	colours = []
	for key in C:
		colour = Colour(department=ICU, description=key)
		colour.set_fromhex(C[key])
		colours.append(colour)

	db.session.add_all(colours + users+[ICU, JR_pool, SR_pool, Con_pool]+Roles+Employees+[rg, roster,ver,ver2]+Shifts+alloc+leaves+requests)#Users+Patients+Studies+Fields+Records)
	db.session.commit()