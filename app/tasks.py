from .models import *
from app import db, g

def push_changes():
    db.session.commit()

# Initial application tasks

def initialise_droster():
    # create blanket permissions
    from .models import _generate_functions, _create_superuser
    _generate_functions()
    _create_superuser()
    push_changes()
    # create 

def create_user(*, username, password, email=None, mobile=None):
    U = User(username=username, email=email, mobile=mobile)
    U.set_password(password)

    push_changes()

def create_department(*, user_id, hr_id, long_name):
    D = Department(hr_id=hr_id, long_name=long_name)

    # permissions

    push_changes()    

def create_employees(*, department_id, given_name, surname, preferred_name=None,
                     payroll_id, novel_login):

    D = Department.get_by_id(department_id)
    E = Employee(department=D,
                 given_name=given_name,
                 surname=surname,
                 preferred_name=preferred_name,
                 payroll_id=payroll_id,
                 novel_login=novel_login)
    
    push_changes()

def claim_employee(*, employee_id, user_id):
    U = User.query.filter_by(user_id=user_id).first()
    E = Employee.query.filter_by(employee_id=employee_id).first()    
    U.claim_employee(E)
    push_changes()

def notify_employee(employee, message):
    raise NotImplementedError

def create_pool(*, department_id, description):
    D = Department.get_by_id(department_id)
    P = Pool(description=description)
    D.add_pool(P)    

    push_changes()

def create_role(*, department_id, description):
    D = Department.get_by_id(department_id)
    R = Role(description=description)
    D.add_role(R)

    push_changes()

def define_role_cover(*, role_id, pool_id):
    R = Role.get_by_id(role_id)
    P = Pool.get_by_id(pool_id)

    R.add_pool(pool=P)

    push_changes()

def create_roster(*, pool_id, start, end):
    P = Pool.get_by_id(pool_id)
    R = Roster(pool=P,
               start=start,
               end=end)
    for employee in P.employees:
        R.add_employee(employee)
    
    push_changes()
    

def delete_roster():
    raise NotImplementedError

def version_roster(*, roster_id):
    pass

def allocate_employee_to_shift(*, roster_version_id, employee_id, shift_id):
    # is that shift currently allocated
    pass
