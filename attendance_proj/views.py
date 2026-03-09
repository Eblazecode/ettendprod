# settings.py
import base64
import os
import logging
import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.management import BaseCommand
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_backends, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.defaultfilters import date
from django.utils import timezone
from psycopg2.extras import RealDictCursor
from .forms import AdminForm, AdminLoginForm, Upload_timetable_form, MachineForm, Upload_registered_students, \
    Upload_staff_events_attendance, Upload_students_events_attendance, Upload_students_database, \
    Upload_staff_records
from datetime import datetime
import psycopg2

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, request

import csv
import pandas as pd
from django.core.cache import cache  # Assuming Django's default caching framework is used
from datetime import date

from .models import Staff_mass_records
import pyexcel_xls as p


# Create your views here.
def index(request):
    return render(request, 'index.html')


def student(request):
    return render(request, 'student.html')


def admin(request):
    return render(request, 'admin.html')


def success_url(request):
    return render(request, 'success_url.html')


def dashboard(request):
    return render(request, 'dashboard.html', {'admin_name': request.session.get('admin_name')})


def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


def success_url(request):
    return render(request, 'success_url.html')


def admin_login(request):
    return render(request, 'admin_login.html')


def time_table(request):
    return render(request, 'time_table.html')


# views.py

# views.py

def admin_register(request):
    if request.method == 'POST':
        print("Form submitted with POST method")
        form = AdminForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            admin = form.save(commit=False)
            admin.set_password(form.cleaned_data['admin_password'])
            admin.save()

            # Get the backend used for authentication
            backend = get_backends()[0]
            admin.backend = f'{backend.__module__}.{backend.__class__.__name__}'

            login(request, admin, backend=admin.backend)
            messages.success(request, 'Account created successfully')
            return redirect('admin_login')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = AdminForm()
    return render(request, 'admin_register.html', {'form': form})


# views.py


def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            try:
                print("Form data (cleaned):", form.cleaned_data)
                ad_email = form.cleaned_data['admin_email']
                ad_password = form.cleaned_data['admin_password']
                admin = authenticate(request, username=ad_email, password=ad_password)
                print("Admin object:", admin)
                if admin is not None:
                    login(request, admin)

                    # Set session data
                    request.session['admin_id'] = admin.id
                    request.session['admin_email'] = admin.admin_email
                    request.session['admin_name'] = f"{admin.admin_fname} {admin.admin_lname}"

                    messages.success(request, 'Login successful')
                    return redirect('dashboard')  # Ensure 'dashboard' is defined in your urls.py
                else:

                    messages.error(request, 'Invalid email or password')
            except KeyError as e:
                print(f"KeyError: {e}")
                messages.error(request, 'Form data error')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Invalid form submission')
    else:
        form = AdminLoginForm()
    return render(request, 'admin_login.html', {'form': form})


# logout view
def admin_logout(request):
    logout(request)
    request.session.flush()  # Clear the session
    return redirect('admin_login')

    # DAPN TIMTABLE UPLOADS


def upload_DAP_timetable(request):
    if request.method == 'POST':
        form = Upload_timetable_form(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            df = pd.read_excel(file, engine='openpyxl')
            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # SAVE THE DATAFRAME TO  A FOLDER

            filename = f'DAP/TimeTable{current_date}.csv'
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            df.to_csv(file_path, index=False)

            messages.success(request, 'Timetable uploaded successfully')
        else:
            messages.error(request, 'Invalid form submission XLSX file required')

    else:
        form = Upload_timetable_form()

    return render(request, 'time_table.html', {'form': form})


# view DAP uploaded timetable

def view_timetable(request):
    # Path to the "timetables" folder

    DAP_folder = os.path.join(settings.MEDIA_ROOT, 'DAP')

    # Ensure the "timetables" directory exists
    if not os.path.exists(DAP_folder):
        messages.error(request, 'No attendance records uploaded yet')
        return render(request, 'timetable_view.html')

    files = os.listdir(DAP_folder)

    # Filter out files that are not CSV files
    csv_files = [file for file in files if file.endswith('.csv')]

    if not csv_files:
        messages.error(request, 'No CSV files found in the directory')
        return render(request, 'timetable_view.html')

    # Find the most recent file based on the modification time
    most_recent_file = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(DAP_folder, x)))

    # Read the most recent CSV file
    most_recent_file_path = os.path.join(DAP_folder, most_recent_file)
    df = pd.read_csv(most_recent_file_path)

    timetable_data = df.to_dict(orient='records')
    return render(request, 'timetable_view.html', {'timetable_data': timetable_data})


# ATTENDANCE RECORDS FROM MACHINE
def machine_attendance_upload(request):
    if request.method == 'POST':
        form = Upload_timetable_form(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']

            df = pd.read_excel(file, engine='openpyxl')
            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # SAVE THE DATAFRAME TO  A FOLDER

            filename = f'timetables/machineattend{current_date}.csv'
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            df.to_csv(file_path, index=False)

            # Save DataFrame to CSV file
            df.to_csv(file_path, index=False)
            quality_assurance_report(request)

            return redirect('success_url')

            #messages.success(request, 'File uploaded successfully')
            #print(f'File saved to {file_path}')  # Debug print


        else:
            #  print(form.errors)  # Debug print for form errors
            messages.error(request, 'Invalid form submission. XLSX file required.')
    else:
        form = MachineForm()

    return render(request, 'machine_attendance.html', {'form': form})


def machine_upload_view(request):
    timetables_folder = os.path.join(settings.MEDIA_ROOT, 'timetables')

    # Ensure the "timetables" directory exists
    if not os.path.exists(timetables_folder):
        messages.error(request, 'No attendance records uploaded yet')
        return render(request, 'machine_upload_view.html')

    files = os.listdir(timetables_folder)

    # Filter out files that are not CSV files
    csv_files = [file for file in files if file.endswith('.csv')]

    if not csv_files:
        messages.error(request, 'No CSV files found in the directory')
        return render(request, 'machine_upload_view.html')

    # Find the most recent file based on the modification time
    most_recent_file = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(timetables_folder, x)))

    # Read the most recent CSV file
    most_recent_file_path = os.path.join(timetables_folder, most_recent_file)
    df = pd.read_csv(most_recent_file_path)

    machine_data = df.to_dict(orient='records')
    return render(request, 'machine_upload_view.html', {'machine_data': machine_data})


# processsing attendance records for quality assurance

def quality_assurance_report(request):
    timetables_folder = os.path.join(settings.MEDIA_ROOT, 'timetables')
    DAP_folder = os.path.join(settings.MEDIA_ROOT, 'DAP')

    # Ensure the "machines records timetables and DAP" directory exists

    if not os.path.exists(timetables_folder) or not os.path.exists(DAP_folder):
        messages.error(request, 'No attendance records uploaded yet')
        return render(request, 'student_attendance_report.html')

    # List CSV files in both directories
    machine_files = [f for f in os.listdir(timetables_folder) if f.endswith('.csv')]
    DAP_files = [f for f in os.listdir(DAP_folder) if f.endswith('.csv')]

    if not machine_files and not DAP_files:
        messages.error(request, 'No CSV files found in the directory')
        return render(request, 'student_attendance_report.html')

    # Find the most recent file based on the modification time
    most_recent_file_machine = max(machine_files, key=lambda x: os.path.getmtime(os.path.join(timetables_folder, x)))
    most_recent_file_DAP = max(DAP_files, key=lambda x: os.path.getmtime(os.path.join(DAP_folder, x)))

    # Read the most recent CSV file
    most_recent_file_path_machine = os.path.join(timetables_folder, most_recent_file_machine)
    most_recent_file_path_DAP = os.path.join(DAP_folder, most_recent_file_DAP)
    df_machine = pd.read_csv(most_recent_file_path_machine)
    df_DAP = pd.read_csv(most_recent_file_path_DAP)

    # Merge the two dataframes; machine data nad DAP  on the 'venue' column
    df_merged = pd.merge(df_machine, df_DAP, on='venue')

    # Save the merged DataFrame to a new CSV file

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'QUALITYASSURANCE/student_merged_attendance_report{current_date}.csv'
    print(f'File saved to {filename}')  # Debug print
    student_attend_merged_file_path = os.path.join(settings.MEDIA_ROOT, filename)
    df_merged.to_csv(student_attend_merged_file_path, index=False)

    # Return the merged DataFrame as a dictionary
    student_attend_merged_data_dict = df_merged.to_dict(orient='records')
    return render(request, 'student_attendance_report.html',
                  {'student_attend_merged_data': student_attend_merged_data_dict})


logger = logging.getLogger(__name__)


# Consolidated CSV reading function

# MAKING NEW CHANGES TO THE VIEWS.PY FILE
# functions to import the courses csv files


def read_csv_to_list(file_path):
    data_list = []
    with open(file_path, 'r', encoding='latin-1') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:
                data_list.append(row[0])  # Append the first column value
    return data_list


# Read each departments and course codes and convert them to a list for department map
def read_department_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_computer_science_courses_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_history_courses_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_economics_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_accounting_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_mass_comm_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_electrical_engr_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_computer_engr_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_pharmacy_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_chemistry_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_education_mgt_csv_to_list(file_path):
    return read_csv_to_list(file_path)


def read_political_science_csv_to_list(file_path):
    return read_csv_to_list(file_path)


# course path to directory
attend_gen_data = os.path.join(settings.MEDIA_ROOT, 'attendance_gen_data')
departments_csv_path = os.path.join(attend_gen_data, 'departments.csv')
computer_science_courses_csv_path = os.path.join(attend_gen_data, 'computer_sci_courses.csv')
computer_engr_courses_csv_path = os.path.join(attend_gen_data, 'comp_engr_courses.csv')
electrical_engr_courses_csv_path = os.path.join(attend_gen_data, 'elect_elcetric_engr.csv')
mass_comm_courses_csv_path = os.path.join(attend_gen_data, 'mass_comm.csv')
economics_courses_csv_path = os.path.join(attend_gen_data, 'economics_courses.csv')
accounting_courses_csv_path = os.path.join(attend_gen_data, 'account_courses.csv')
education_mgt_courses_csv_path = os.path.join(attend_gen_data, 'edu_mgt_courses.csv')
chemistry_courses_csv_path = os.path.join(attend_gen_data, 'chemistry_courses.csv')
history_courses_csv_path = os.path.join(attend_gen_data, 'hist_inter_rel.csv')
political_science_courses_csv_path = os.path.join(attend_gen_data, 'political_sci_course.csv')

# course codes conversion to list  for each
computer_sci_course_list = read_computer_science_courses_csv_to_list(computer_science_courses_csv_path)
history_courses_list = read_history_courses_csv_to_list(history_courses_csv_path)
economics_courses_list = read_economics_csv_to_list(economics_courses_csv_path)
accounting_courses_list = read_accounting_csv_to_list(accounting_courses_csv_path)
mass_comm_courses_list = read_mass_comm_csv_to_list(mass_comm_courses_csv_path)
electrical_engr_courses_list = read_electrical_engr_csv_to_list(electrical_engr_courses_csv_path)
computer_engr_courses_list = read_computer_engr_csv_to_list(computer_engr_courses_csv_path)
chemistry_course_list = read_chemistry_csv_to_list(chemistry_courses_csv_path)
education_mgt_course_list = read_education_mgt_csv_to_list(education_mgt_courses_csv_path)
political_science_course_list = read_political_science_csv_to_list(political_science_courses_csv_path)

departments_list = read_department_csv_to_list(departments_csv_path)

levels_list = [100, 200, 300, 400, 500]

department_course_map = {
    "Political Science and Diplomacy": political_science_course_list,
    "Economics": economics_courses_list,
    "Industrial Chemistry": ["IC101", "IC102", "IC201"],
    "Physics with Electronics": ["PWE101", "PWE102", "PWE201"],
    "Applied Microbiology": ["AM101", "AM102", "AM201"],
    "Philosophy": ["PHI101", "PHI102", "PHI201"],
    "Computer Science": computer_sci_course_list,
    "Mass Communication": mass_comm_courses_list,
    "English and Literary Studies": ["ELS101", "ELS102", "ELS201"],
    "History and International Relations": history_courses_list,
    "Marketing and Advertising": ["MA101", "MA102", "MA201"],
    "Accounting": accounting_courses_list,
    "Theology": ["THE101", "THE102", "THE201"],
    "English Education": ["EE101", "EE102", "EE201"],
    "Economics Education": ["EDE101", "EDE102", "EDE201"],
    "Chemistry Education": ["CE101", "CE102", "CE201"],
    "Physics Education": ["PE101", "PE102", "PE201"],
    "Educational Management": education_mgt_course_list,
    "Business Administration": ["BA101", "BA102", "BA201"],
    "Entrepreneurial Studies": ["ES101", "ES102", "ES201"],
    "Peace And Conflict Studies": ["PACS101", "PACS102", "PACS201"],
    "B.Eng Computer Engineering": computer_engr_courses_list,
    "B.Eng Electrical and Electronic Engineering": electrical_engr_courses_list,
    "Law": ["LAW101", "LAW102", "LAW201"],
    "SOFTWARE ENGINEERING": ["SE101", "SE102", "SE201"],
    "Nursing": ["NUR101", "NUR102", "NUR201"],
    "Pharmacy": ["PHAR101", "PHAR102", "PHAR201"],
    "Medical Laboratory Sciences": ["MLS101", "MLS102", "MLS201"],
    "Sacred Theology": ["ST101", "ST102", "ST201"],
    "Computer science Education": ["CSE101", "CSE102", "CSE201"],
    "Medicine and Surgery": ["MS101", "MS102", "MS201"],
    "Religious Education": ["RE101", "RE102", "RE201"],
    "Public Administration": ["PA101", "PA102", "PA201"],
}


def select_course(request):
    return render(request, 'select_course.html')


@csrf_exempt
def get_courses(request, department):
    courses = department_course_map.get(department, [])
    return JsonResponse({'courses': courses})


@csrf_exempt
def process_selection(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        course = request.POST.get('course')
        # Process the selected department and course
        return JsonResponse({'department': department, 'course': course})


@csrf_exempt
def process_selection(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        course = request.POST.get('course_code')
        level = request.POST.get('Level')  # Ensure this matches the form field name exactly

        request.session['department'] = department
        request.session['course'] = course
        request.session['Level'] = level

        try:
            level_int = int(level) if level is not None else 0  # Assuming 0 as a default, adjust as needed
        except ValueError:
            level_int = 0  # Default if conversion fails
            messages.error(request, "Invalid level value. Using default.")

        try:
            filtered_data = load_and_filter_data(department, level_int, course)
            return render(request, 'student_attendance_report.html', {'filtered_data': filtered_data})
        except Exception as e:
            messages.error(request, str(e))
            # If an error occurs, still render the page but without filtered_data
            return render(request, 'student_attendance_report.html',
                          {'department': department, 'course': course, 'level': level})
    # If not POST, or after handling POST, render a default or error page
    return render(request, 'some_default_or_error_page.html')


# upload department and course codes


def generate_attendance(request):
    # Assuming these are set earlier in the function
    department = request.session.get('department')
    course = request.session.get('course')
    level_int = int(request.session.get('level', 0))  # Default to 0 if not set

    try:
        # Assuming 'load_and_filter_data' returns a DataFrame
        filtered_data = load_and_filter_data(department, level_int, course)

        # Render the page with the filtered data
        return render(request, 'student_attendance_report.html',
                      {'filtered_data': filtered_data.to_dict(orient='records')})

    except Exception as e:
        messages.error(request, str(e))

        print("No data found for the given department, level, and course code")
        return render(request, 'student_attendance_report.html')


# update comp_sci_100l table wth filtered data


from pathlib import Path


def save_filtered_data(department, level, course_code, filtered_df, folder_name):
    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_dir = Path(settings.MEDIA_ROOT) / f'WEEKLY_ATTENDANCE/{folder_name}/{level}l'
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / f'{course_code}_{current_date}.csv'

    if file_path.exists():
        existing_df = pd.read_csv(file_path)
        if 'attendance_score' not in filtered_df.columns:
            filtered_df['attendance_score'] = 1
        merged_df = pd.merge(existing_df, filtered_df, on='Userprofile', how='outer')
        merged_df['attendance_score'] = merged_df['attendance_score_x'].fillna(0) + merged_df[
            'attendance_score_y'].fillna(1)
        merged_df.drop(columns=['attendance_score_x', 'attendance_score_y'], inplace=True)
        merged_df.to_csv(file_path, index=False)
    else:
        if 'attendance_score' not in filtered_df.columns:
            filtered_df['attendance_score'] = 1
        filtered_df.to_csv(file_path, index=False)

    print(f'File saved to {file_path}')


def load_and_filter_data(department, level, course_code):
    column_types = {
        'ID': str, 'Name': str, 'Dept': str, 'Userprofile': str, 'SN': int,
        'Coursetitle': str, 'CourseCode': str, 'Level': int,
    }

    quality_folder = Path(settings.MEDIA_ROOT) / 'QUALITYASSURANCE'
    most_recent_file = max(quality_folder.glob('*'), key=lambda x: x.stat().st_mtime)

    if not most_recent_file:
        print("No attendance records uploaded yet")
        return

    df = pd.read_csv(most_recent_file, delimiter=',', dtype=column_types, engine='python', encoding='latin-1')

    department = department.strip().upper()
    course_code = course_code.strip().upper()

    dept_filtered = df['Dept'].str.strip().str.upper() == department
    level_filtered = df['Level'] == level
    course_code_filtered = df['CourseCode'].str.strip().str.upper() == course_code

    filtered_df = df[dept_filtered & level_filtered & course_code_filtered]

    if filtered_df.empty:
        raise ValueError('No data found for the given department, level, and course code')

    folder_map = {
        ('COMPUTER SCIENCE', 100): 'computer_sci/100l',
        ('COMPUTER SCIENCE', 200): 'computer_sci/200l',
        ('COMPUTER SCIENCE', 400): 'computer_sci/400l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 100): 'political_sci/100l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 200): 'political_sci/200l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 300): 'political_sci/300l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 400): 'political_sci/400l',
    }

    # database tables folder_map for each department and level
    db_tables_folder_map = {
        ('COMPUTER SCIENCE', 100): 'attendance_proj_comp_sci_100l',
        ('COMPUTER SCIENCE', 200): 'attendance_proj_comp_sci_200l',
        ('COMPUTER SCIENCE', 300): 'attendance_proj_comp_sci_300l',
        ('COMPUTER SCIENCE', 400): 'attendance_proj_comp_sci_400l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 100): 'attendance_proj_pol_sci_100l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 200): 'attendance_proj_pol_sci_200l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 300): 'attendance_proj_pol_sci_300l',
        ('POLITICAL SCIENCE AND DIPLOMACY', 400): 'attendance_proj_pol_sci_400l',
    }

    folder_name = folder_map.get((department, level))

    if folder_name:
        save_filtered_data(department, level, course_code, filtered_df, folder_name)

        # Update the database with the new attendance scores for each course in department using mat no and course code


    else:
        print("Invalid department, level, or course code")

    weekly_attendance()
    return filtered_df.to_dict(orient='records')


# UNSCHEDULED EVENTS ATTENDANCE PROCESSING CAPTURED BY MACHINE HANDLING
def unscheduled_events_attendance(request):
    return render(request, 'unscheduled_events.html')


# TRACKING  ATTENDANCE CRITERIA FOR SELCETING DEPT, COURSE AND LEVEL

@csrf_exempt
def track_attendance(request):
    if request.method == 'POST':
        department = request.POST.get('department1')
        course = request.POST.get('course_code')
        level = request.POST.get('Level')
        matric_num = request.POST.get('matric_num')
        # Ensure this matches the form field name exactly

        request.session['department'] = department
        request.session['course'] = course
        request.session['Level'] = level
        request.session['matric_num'] = matric_num

        try:
            level_int = int(level) if level is not None else 0  # Assuming 0 as a default, adjust as needed
        except ValueError:
            level_int = 0  # Default if conversion fails
            messages.error(request, "Invalid level value. Using default.")

        try:
            filtered_data = load_and_filter_data(department, level_int, course)
            update_each_course_attendance_score(department, level, course, filtered_data)
            return render(request, 'summary_attend.html', {'filtered_data': filtered_data})

        except Exception as e:
            messages.error(request, str(e))
            # If an error occurs, still render the page but without filtered_data
            return render(request, 'summary_attend.html',
                          {'department': department, 'course': course, 'level': level})
    else:
        # If not POST, or after handling POST, render a default or error page
        return render(request, 'some_default_or_error_page.html')


def weekly_attendance():
    folder_path = 'DAP/FILTERED_DATA/computer_sci/100l'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    dataframes = [pd.read_csv(os.path.join(folder_path, file), low_memory=False) for file in csv_files]
    cleaned_dataframes = [df.dropna(axis=1, how='all') for df in dataframes]
    merged_df = pd.concat(cleaned_dataframes)

    summed_df = merged_df.groupby('Userprofile')['attendance_score'].sum().reset_index()

    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_dir = os.path.join(settings.MEDIA_ROOT, 'WEEKLY_ATTENDANCE/computer_science')
    os.makedirs(file_dir, exist_ok=True)
    filename = f'comp_sci_100_{current_date}.csv'
    file_path = os.path.join(file_dir, filename)
    summed_df.to_csv(file_path, index=False)

    comp_sci_100l_students = [f for f in os.listdir(file_dir) if f.endswith('.csv')]
    most_recent_file = max(comp_sci_100l_students, key=lambda f: os.path.getmtime(os.path.join(file_dir, f)))

    most_recent_tot_score_path_comp_sci_100l = os.path.join(file_dir, most_recent_file)
    df_comp_sci_100l = pd.read_csv(most_recent_tot_score_path_comp_sci_100l)

    if df_comp_sci_100l.empty:
        print("DataFrame is empty. No data to update.")
        return

    print("File uploaded and processed successfully NOW.")
    print(df_comp_sci_100l.head())

    conn = psycopg2.connect(
        dbname='ettend_db',
        user='postgres',
        password='blaze',
        host='localhost',
        port='5432'
    )
    cur = conn.cursor()

    for index, row in df_comp_sci_100l.iterrows():
        query = """
        UPDATE ettend_db.public.attendance_proj_comp_sci_100l
        SET 
            total_attendance_score = %s,
            week = %s
        WHERE matric_num = %s
        """
        print(cur.mogrify(query, (row["attendance_score"], 1, row['Userprofile'])))
        cur.execute(query, (row["attendance_score"], 1, row['Userprofile']))
        print(f"Rows updated: {cur.rowcount}")

    conn.commit()
    cur.close()
    conn.close()
    print("Database updated successfully")


def update_each_score(request):
    render(request, 'update_weekly_attendance.html')


def update_each_course_attendance_score(department, level, course_code, filtered_df):
    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_dir = Path(settings.MEDIA_ROOT) / f'WEEKLY_ATTENDANCE/{department.lower().replace(" ", "_")}/{level}l'
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / f'{course_code}_{current_date}.csv'
    filtered_df.to_csv(file_path, index=False)

    # Connect to the PostgreSQL database
    try:
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        # Sanitize table name inputs
        table_name = f'attendance_proj_{department.lower().replace(" ", "_")}_{level}l'
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                    (table_name,))
        table_columns = [row[0] for row in cur.fetchall()]

        # Compare table columns and DataFrame columns
        df_columns = filtered_df.columns.tolist()
        common_columns = set(table_columns).intersection(df_columns)

        if not common_columns:
            print("No common columns found. No updates will be performed.")
            return

        # Bulk update data
        for index, row in filtered_df.iterrows():
            set_clause = ", ".join([f"{col} = %s" for col in common_columns])
            query = f"""
            UPDATE ettend_db.public.{table_name}
            SET {set_clause}
            WHERE matric_num = %s AND course_code = %s
            """
            values = [row[col] for col in common_columns] + [row['matric_num'], course_code]
            cur.execute(query, values)
            print(f"Rows updated: {cur.rowcount}")

        conn.commit()
        print("Database updated successfully")

    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
    finally:
        cur.close()
        conn.close()


# CREATE THE DATABASE RECORDS OF REGISTRED STUDENTS FROM EACH LEVEL IN A DEPARTMENT FROM CSV FILE UPLOAD
# consider the department and level of the students
# update the database


@csrf_exempt
def Update_weekely_attendance_DB(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        level = request.POST.get('Level')
        form = Upload_registered_students(request.POST, request.FILES)

        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        # Save the uploaded file to a folder
        if form.is_valid():
            if 'file' in form.cleaned_data:
                try:
                    file = form.cleaned_data['file']
                    df = pd.read_excel(file, engine='openpyxl')
                    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                except Exception as e:
                    messages.error(request, f"An error occurred while processing the file: {e}")

                # List CSV files in the directories
                try:
                    level_int = int(level) if level else 0  # Assuming 0 as a default, adjust as needed
                except ValueError:
                    level_int = 0  # Default if conversion fails
                    messages.error(request, "Invalid level value. Using default.")

                print("debugging: level and dept present in the request", department, level, form.errors)

                # STUDENT RECORDS UPLOAD TO DATABASE
                # COMPUTER SCIENCE 100L STUDENTS ONLY

                if department == 'Computer Science':
                    if level_int == 100:

                        comp_sci_100l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                       'course_registeration/computer_science/100l')
                        comp_sci_100l_students_filename = f'computer_science_100l_{current_date}.csv'
                        comp_sci_100l_students_file_path = os.path.join(comp_sci_100l_students_dir_path,
                                                                        comp_sci_100l_students_filename)

                        df.to_csv(comp_sci_100l_students_file_path, index=False)

                        comp_sci_100l_students = [f for f in os.listdir(comp_sci_100l_students_dir_path) if
                                                  f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(comp_sci_100l_students, key=lambda f: os.path.getmtime(
                            os.path.join(comp_sci_100l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_comp_sci_100l = os.path.join(comp_sci_100l_students_dir_path,
                                                                           most_recent_file)
                        df_comp_sci_100l = pd.read_csv(most_recent_file_path_comp_sci_100l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_comp_sci_100l.head())

                        # Upload most recent file to the computer_sci_100L DATABASE

                        # Update the database table field only  where table field matches the course_code
                        for index, row in df_comp_sci_100l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_comp_sci_100l 
                                (biometric_id, student_name, "CSC_101", "CSC_102", "CSC_105", "CSC_111", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["CSC101"], row["CSC102"], row["CSC105"],
                                 row["CSC111"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                        conn.commit()
                        cur.close()
                        conn.close()
                        print("Database updated successfully")

                    # COMPUTER SCIENCE 200L STUDENTS ONLY
                    elif level_int == 200:
                        comp_sci_200l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                       'course_registeration/computer_science/200l')
                        comp_sci_200l_students_filename = f'computer_science_200l_{current_date}.csv'
                        comp_sci_200l_students_file_path = os.path.join(comp_sci_200l_students_dir_path,
                                                                        comp_sci_200l_students_filename)

                        df.to_csv(comp_sci_200l_students_file_path, index=False)

                        comp_sci_200l_students = [f for f in os.listdir(comp_sci_200l_students_dir_path) if
                                                  f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(comp_sci_200l_students, key=lambda f: os.path.getmtime(
                            os.path.join(comp_sci_200l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_comp_sci_200l = os.path.join(comp_sci_200l_students_dir_path,
                                                                           most_recent_file)
                        df_comp_sci_200l = pd.read_csv(most_recent_file_path_comp_sci_200l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_comp_sci_200l.head())

                        # Upload most recent file to the computer_sci_200L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_comp_sci_200l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_comp_sci_200l (biometric_id, student_name, "CSC_201", "CSC_202", "CSC_203", "CSC_204", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["CSC201"], row["CSC"], row["CSC203"],
                                 row["CSC204"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")

                    # COMPUTER SCIENCE 300L STUDENTS ONLY
                    elif level_int == 300:
                        comp_sci_300l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                       'course_registeration/computer_science/300l')
                        comp_sci_300l_students_filename = f'computer_science_300l_{current_date}.csv'
                        comp_sci_300l_students_file_path = os.path.join(comp_sci_300l_students_dir_path,
                                                                        comp_sci_300l_students_filename)

                        df.to_csv(comp_sci_300l_students_file_path, index=False)

                        comp_sci_300l_students = [f for f in os.listdir(comp_sci_300l_students_dir_path) if
                                                  f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(comp_sci_300l_students, key=lambda f: os.path.getmtime(
                            os.path.join(comp_sci_300l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_comp_sci_300l = os.path.join(comp_sci_300l_students_dir_path,
                                                                           most_recent_file)
                        df_comp_sci_300l = pd.read_csv(most_recent_file_path_comp_sci_300l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_comp_sci_300l.head())

                        # Upload most recent file to the computer_sci_300L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_comp_sci_300l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_comp_sci_300l (biometric_id, student_name, "CSC_301", "CSC_302", "CSC_303", "CSC_304", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["CSC301"], row["CSC302"], row["CSC303"],
                                 row["CSC304"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close

                            print("Database updated successfully")

                    # COMPUTER SCIENCE 400L STUDENTS ONLY
                    elif level_int == 400:
                        comp_sci_400l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                       'course_registeration/computer_science/400l')
                        comp_sci_400l_students_filename = f'computer_science_400l_{current_date}.csv'
                        comp_sci_400l_students_file_path = os.path.join(comp_sci_400l_students_dir_path,
                                                                        comp_sci_400l_students_filename)

                        df.to_csv(comp_sci_400l_students_file_path, index=False)

                        comp_sci_400l_students = [f for f in os.listdir(comp_sci_400l_students_dir_path) if
                                                  f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(comp_sci_400l_students, key=lambda f: os.path.getmtime(
                            os.path.join(comp_sci_400l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_comp_sci_400l = os.path.join(comp_sci_400l_students_dir_path,
                                                                           most_recent_file)
                        df_comp_sci_400l = pd.read_csv(most_recent_file_path_comp_sci_400l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_comp_sci_400l.head())

                        # Upload most recent file to the computer_sci_400L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_comp_sci_400l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_comp_sci_400l (biometric_id, student_name, "CSC_401", "CSC_402", "CSC_403", "CSC_404", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["CSC401"], row["CSC402"], row["CSC403"],
                                 row["CSC404"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")

                # FOR POLITICAL SCIENCE AND DIPLOMACY DEPARTMENT
                elif department == 'Political Science and Diplomacy':
                    if level_int == 100:
                        political_sci_100l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                            'course_registeration/political_science/100l')
                        political_sci_100l_students_filename = f'political_sci_100l_{current_date}.csv'
                        political_sci_100l_students_file_path = os.path.join(political_sci_100l_students_dir_path,
                                                                             political_sci_100l_students_filename)

                        df.to_csv(political_sci_100l_students_file_path, index=False)

                        political_sci_100l_students = [f for f in os.listdir(political_sci_100l_students_dir_path) if
                                                       f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(political_sci_100l_students, key=lambda f: os.path.getmtime(
                            os.path.join(political_sci_100l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_political_sci_100l = os.path.join(political_sci_100l_students_dir_path,
                                                                                most_recent_file)
                        df_political_sci_100l = pd.read_csv(most_recent_file_path_political_sci_100l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_political_sci_100l.head())

                        # Upload most recent file to the political_sci_100L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_political_sci_100l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_pol_sci_100l (biometric_id, student_name, "POL_101", "POL_102", "POL_103", "POL_104", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["PSC101"], row["PSC102"], row["PSC103"],
                                 row["PSC104"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")

                    # POLITICAL SCIENCE AND DIPLOMACY 200L STUDENTS ONLY
                    elif level_int == 200:
                        political_sci_200l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                            'course_registeration/political_science/200l')
                        political_sci_200l_students_filename = f'political_sci_200l_{current_date}.csv'
                        political_sci_200l_students_file_path = os.path.join(political_sci_200l_students_dir_path,
                                                                             political_sci_200l_students_filename)

                        df.to_csv(political_sci_200l_students_file_path, index=False)

                        political_sci_200l_students = [f for f in os.listdir(political_sci_200l_students_dir_path) if
                                                       f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(political_sci_200l_students, key=lambda f: os.path.getmtime(
                            os.path.join(political_sci_200l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_political_sci_200l = os.path.join(political_sci_200l_students_dir_path,
                                                                                most_recent_file)
                        df_political_sci_200l = pd.read_csv(most_recent_file_path_political_sci_200l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_political_sci_200l.head())

                        # Upload most recent file to the political_sci_200L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_political_sci_200l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_pol_sci_200l (biometric_id, student_name, "POL_201", "POL_202", "POL_203", "POL_204", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["POL201"], row["POL202"], row["POL203"],
                                 row["POL204"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")

                    # POLITICAL SCIENCE AND DIPLOMACY 300L STUDENTS ONLY
                    elif level_int == 300:
                        political_sci_300l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                            'course_registeration/political_science/300l')
                        political_sci_300l_students_filename = f'political_sci_300l_{current_date}.csv'
                        political_sci_300l_students_file_path = os.path.join(political_sci_300l_students_dir_path,
                                                                             political_sci_300l_students_filename)

                        df.to_csv(political_sci_300l_students_file_path, index=False)

                        political_sci_300l_students = [f for f in os.listdir(political_sci_300l_students_dir_path) if
                                                       f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(political_sci_300l_students, key=lambda f: os.path.getmtime(
                            os.path.join(political_sci_300l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_political_sci_300l = os.path.join(political_sci_300l_students_dir_path,
                                                                                most_recent_file)
                        df_political_sci_300l = pd.read_csv(most_recent_file_path_political_sci_300l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_political_sci_300l.head())

                        # Upload most recent file to the political_sci_300L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_political_sci_300l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_pol_sci_300l (biometric_id, student_name, "POL_301", "POL_302", "POL_303", "POL_304", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["POL301"], row["POL302"], row["POL303"],
                                 row["POL304"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")

                    # POLITICAL SCIENCE AND DIPLOMACY 400L STUDENTS ONLY
                    elif level_int == 400:
                        political_sci_400l_students_dir_path = os.path.join(settings.MEDIA_ROOT,
                                                                            'course_registeration/political_science/400l')
                        political_sci_400l_students_filename = f'political_sci_400l_{current_date}.csv'
                        political_sci_400l_students_file_path = os.path.join(political_sci_400l_students_dir_path,
                                                                             political_sci_400l_students_filename)

                        df.to_csv(political_sci_400l_students_file_path, index=False)

                        political_sci_400l_students = [f for f in os.listdir(political_sci_400l_students_dir_path) if
                                                       f.endswith('.csv')]

                        # Find the most recent file based on the modification time
                        most_recent_file = max(political_sci_400l_students, key=lambda f: os.path.getmtime(
                            os.path.join(political_sci_400l_students_dir_path, f)))

                        # Read the most recent CSV file
                        most_recent_file_path_political_sci_400l = os.path.join(political_sci_400l_students_dir_path,
                                                                                most_recent_file)
                        df_political_sci_400l = pd.read_csv(most_recent_file_path_political_sci_400l)
                        messages.success(request, "File uploaded and processed successfully NOW.")
                        print(df_political_sci_400l.head())

                        # Upload most recent file to the political_sci_400L DATABASE

                        # Update the database with the new attendance scores
                        for index, row in df_political_sci_400l.iterrows():
                            cur.execute(
                                """
                                INSERT INTO ettend_db.public.attendance_proj_pol_sci_400l (biometric_id, student_name, "POL_401", "POL_402", "POL_403", "POL_404", level, total_attendance_score, week, matric_num)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (row['BIOMETRICS_ID'], row['STUDENT_NAME'], row["POL401"], row["POL402"], row["POL403"],
                                 row["POL404"], level_int, 0, 0, row['MATRIC_NO.'])
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            print("Database updated successfully")



                else:
                    messages.error(request, "Invalid department or level.")
        else:
            messages.error(request, "Invalid form submission.")

    form = Upload_registered_students()
    return render(request, 'departmental_students_upload.html', {'form': form})


def summary_attendance(request):
    """
    Generates a summary of attendance for a given department, course, and level.
    Renders a page with the filtered attendance data or an error message.

    :param request: HttpRequest object containing session data for department, course, and level.
    :return: HttpResponse object rendering the appropriate template.
    """
    # Retrieve session data with defaults
    department = request.session.get('department', None)
    course = request.session.get('course', None)
    level_int = int(request.session.get('level', 0))  # Default to 0 if not set or found

    try:
        # Validate session data
        if not department or not course:
            raise ValueError("Missing department or course information in session.")

        # Load and filter data based on session parameters
        filtered_data = load_and_filter_data(department, level_int, course)

        # Render the page with the filtered data
        return render(request, 'summary_attend.html', {'filtered_data': filtered_data.to_dict(orient='records')})

    except Exception as e:
        # Log the error and show an error message to the user
        logger.error(f"Error generating attendance summary: {str(e)}")
        messages.error(request, str(e))
        return render(request, 'summary_attend.html')


# GENERATE STUDENTS ATTENDANCE SCORECARD FOR THE WEEK USING STORED RECORDS IN THE DATABASE
# qr code generator to authenticate the student scorecard
# qr code generator to authenticate the student scorecard
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str


def attendance_score_card(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        level = request.POST.get('Level')
        matric_num = request.POST.get('matric_num')

        print(department, level, matric_num)

        try:
            level_int = int(level) if level else 0
        except ValueError:
            level_int = 0

        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )

        # for computer science department
        try:
            if department == "Computer Science":
                cur = conn.cursor(cursor_factory=RealDictCursor)
                if level_int == 100:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_comp_sci_100l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 200:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_comp_sci_200l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 300:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_comp_sci_300l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 400:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_comp_sci_400l WHERE matric_num = %s",
                        (matric_num,)
                    )
                else:
                    raise ValueError('Invalid level selected')
                student_data = cur.fetchall()
                for student in student_data:
                    total_possible_score = 15  # or whatever the total possible score is
                    student['attendance_percentage'] = (student['total_attendance_score'] / total_possible_score) * 100
                    student["department"] = department
                    student["absents"] = total_possible_score - student['total_attendance_score']
                    # PERCENTAGE ABSENTS
                    student["absent_percentage"] = (student["absents"] / total_possible_score) * 100
                    # todays date
                    student["date"] = datetime.now().strftime('%Y-%m-%d')
                    qr_data = f"{student['matric_num']} {student['student_name']} {student['attendance_percentage']}"
                    student['qr_code'] = generate_qr_code(qr_data)
                cur.close()
                conn.close()

                if not student_data:
                    raise ValueError('No data found for the given department, level, and matric number')

                return render(request, 'scorecard.html', {'student_data': student_data})

            # for political science department
            elif department == "Political Science and Diplomacy":
                cur = conn.cursor(cursor_factory=RealDictCursor)
                if level_int == 100:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_pol_sci_100l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 200:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_pol_sci_200l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 300:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_pol_sci_300l WHERE matric_num = %s",
                        (matric_num,)
                    )
                elif level_int == 400:
                    cur.execute(
                        "SELECT * FROM ettend_db.public.attendance_proj_pol_sci_400l WHERE matric_num = %s",
                        (matric_num,)
                    )
                else:
                    raise ValueError('Invalid level selected')
                student_data = cur.fetchall()
                for student in student_data:
                    total_possible_score = 15
                    student['attendance_percentage'] = (student['total_attendance_score'] / total_possible_score) * 100
                    student["department"] = department
                    student["absents"] = total_possible_score - student['total_attendance_score']
                    # PERCENTAGE ABSENTS
                    student["absent_percentage"] = (student["absents"] / total_possible_score) * 100
                    # todays date
                    student["date"] = datetime.now().strftime('%Y-%m-%d')
                    qr_data = f"{student['matric_num']} {student['student_name']} {student['attendance_percentage']}"
                    student['qr_code'] = generate_qr_code(qr_data)
                cur.close()
                conn.close()
                if not student_data:
                    raise ValueError('No data found for the given department, level, and matric number')
                return render(request, 'scorecard.html', {'student_data': student_data})

            else:
                raise ValueError('Invalid department selected')

        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'scorecard.html')

    # Return a default response if the request method is not POST
    return render(request, 'scorecard.html')


#  upload staff biometric data captured   attendance records AND POPULATE THE DATABASE

def staff_biometrics_upload(request):
    if request.method == 'POST':
        form = Upload_timetable_form(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']

            df = pd.read_excel(file, engine='openpyxl')
            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # SAVE THE DATAFRAME TO A FOLDER

            filename = f'STAFF_DATA/staff_biometrics_data{current_date}.csv'
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            df.to_csv(file_path, index=False)

            # Ensure the "STAFF_DATA" directory exists
            staff_biometrics_dir = os.path.join(settings.MEDIA_ROOT, 'STAFF_DATA')
            if not os.path.exists(staff_biometrics_dir):
                os.makedirs(staff_biometrics_dir)

            # List CSV files in the directory
            staff_biometrics = [f for f in os.listdir(staff_biometrics_dir) if f.endswith('.csv')]

            # Check if the list is empty
            if not staff_biometrics:
                raise ValueError("No CSV files found in the directory")

            # Find the most recent file based on the modification time
            most_recent_file = max(staff_biometrics,
                                   key=lambda f: os.path.getmtime(os.path.join(staff_biometrics_dir, f)))

            # Read the most recent CSV file
            most_recent_file_path = os.path.join(staff_biometrics_dir, most_recent_file)
            df_staff_biometrics = pd.read_csv(most_recent_file_path)
            print(df_staff_biometrics.head())
            # print the head() of the staffid column
            print(df_staff_biometrics['staffid'].head())

            # extract staff ID S
            extract_staff_department(df_staff_biometrics)

            return redirect('success_url')

        else:
            messages.error(request, 'Invalid form submission. XLSX file required.')
    else:
        form = MachineForm()

    return render(request, 'staff_upload.html', {'form': form})


def extract_staff_department(staff_data):
    # Check if the 'staffid' column exists in the DataFrame
    if 'staffid' not in staff_data.columns:
        raise KeyError("The 'staffid' column is missing from the DataFrame")

    # Department mappings
    department_map = {
        'BCH': 'Biochemistry',
        'MCB': 'Microbiology',
        'PHY': 'Physics',
        'CHM': 'Chemistry',
        'CSC': 'Computer Science',
        'EEG': 'Electrical Engineering',
        'ECO': 'Economics',
        'BSR': 'Biological Sciences',
        'REG': 'Registry',
        'MDC': 'Medical Sciences',
        'MTH': 'Mathematics',
        'ENG': 'English',
        'GEO': 'Geography',
        'HIS': 'History',
        'LAW': 'Law',
        'POL': 'Political Science',
        'SOC': 'Sociology',
        'ACC': 'Accounting',
        'BUS': 'Business Administration',
        'MKT': 'Marketing',
        'FIN': 'Finance',
        'AGR': 'Agriculture',
        'ARC': 'Architecture',
        'CIV': 'Civil Engineering',
        'MEC': 'Mechanical Engineering',
        'CHE': 'Chemical Engineering',
        'NUR': 'Nursing',
        'PHR': 'Pharmacy',
        'DNT': 'Dentistry',
        'MED': 'Medicine',
        'VET': 'Veterinary Medicine',
        'EDU': 'Education',
        'ART': 'Fine Arts',
        'MUS': 'Music',
        'THE': 'Theology',
        'PHL': 'Philosophy',
        'REL': 'Religious Studies',
        'PSY': 'Psychology',
        'BIO': 'Biology',
        'GNS': 'General Studies',
        'SOC': 'Sociology',
        'COM': 'Communication',
        'PAD': 'Public Administration',
        'GEO': 'Geography and Planning',
        'STA': 'Statistics',
        'PHE': 'Physical & Health Education',
        'FSN': 'Food Science and Nutrition',
        'FST': 'Food Science and Technology',
        'BMS': 'Basic Medical Sciences',
        'CPE': 'Computer Engineering',
        'ASE': 'Aerospace Engineering',
        'MRE': 'Marine Engineering',
        'MET': 'Metallurgical Engineering',
        'MAC': 'Mass Communication',
        'PUB': 'Public Admin',
        'SEN': 'software engineering',
        'BFN': 'Banking and Finance',
        'HIR': 'History intern Rel',
        'MAT': 'Materials Science',
        'OPT': 'Optometry',
        'SUR': 'Surveying and Geoinformatics',
        'QSM': 'Quantity Surveying',
        'URP': 'Urban and Regional Planning',
        'EST': 'Estate Management',
        'FOR': 'Forestry',
        'HMT': 'Hospitality and Tourism',
        'HRM': 'Human Resource Management',
        'PRS': 'Pharmaceutical Sciences',
        'GDL': 'Guidance and Counselling',
        'LIT': 'Literature',
        'LIN': 'Linguistics',
        'IRP': 'International Relations and Diplomacy',
    }

    # Initialize the 'dept' column with empty strings
    staff_data['dept'] = ''

    # Define a function to extract and map the department code
    def map_department(staff_data):
        parts = staff_data.split('/')
        if len(parts) >= 2:
            department_code = parts[1]
            return department_map.get(department_code, 'Not found')
        return 'Not found'

    # Apply the function to the 'staffid' column to populate the 'dept' column
    staff_data['dept'] = staff_data['staffid'].apply(map_department)
    # SAVE THE MOST RECENT FILE TO THE STAFF_DATA_UPDATED FOLDER
    save_updated_staff_data(staff_data)

    # Optional: Print the first few rows to verify (remove or comment for production)
    print(staff_data.head())
    # upload staff_ids

    return staff_data


def save_updated_staff_data(staff_data):
    # Define the path to the STAFF_DATA_UPDATED folder
    updated_folder = os.path.join(settings.MEDIA_ROOT, 'STAFF_DATA_UPDATED')

    # Ensure the folder exists
    os.makedirs(updated_folder, exist_ok=True)

    # Define the filename with the current timestamp
    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'staff_data_updated_{current_date}.csv'
    file_path = os.path.join(updated_folder, filename)

    # Save the updated DataFrame to the specified path
    staff_data.to_csv(file_path, index=False)
    print(f'Updated staff data saved to {file_path}')


#view upload


import os
import psycopg2
import pandas as pd
from django.conf import settings


import os
import pandas as pd
import psycopg2
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages

def staff_biometrics_upload_view(request):
    # Define the path to the STAFF_DATA_UPDATED folder
    updated_folder = os.path.join(settings.MEDIA_ROOT, 'STAFF_DATA_UPDATED')

    # Ensure the folder exists
    if not os.path.exists(updated_folder):
        return render(request, 'staff_view_upload.html', {'error': 'No updated staff data found'})

    # List all CSV files in the folder
    csv_files = [f for f in os.listdir(updated_folder) if f.endswith('.csv')]

    if not csv_files:
        return render(request, 'staff_view_upload.html', {'error': 'No CSV files found in the directory'})

    # Find the most recent file based on the modification time
    most_recent_file = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(updated_folder, x)))

    # Read the most recent CSV file into a DataFrame
    most_recent_file_path = os.path.join(updated_folder, most_recent_file)

    try:
        staff_data = pd.read_csv(most_recent_file_path)
    except Exception as e:
        return render(request, 'staff_view_upload.html', {'error': f'Error reading CSV file: {e}'})

    # Convert DataFrame to dictionary
    staff_data_dict = staff_data.to_dict(orient='records')

    # Connect to the database
    try:
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        # Iterate over the staff data and insert or update each row into the database
        for index, row in staff_data.iterrows():
            id = row.get('ID', 'N/A')
            staff_id = row.get('staffid', 'N/A')
            staff_name = row.get('Name', 'Unknown')
            department = row.get('dept', 'Unknown')
            staff_score = 1
            attendance_status = 1
            remark = "absent"

            # Assign default date if missing
            conference_date = row.get('conference_date', datetime.now().strftime("%Y-%m-%d"))

            cur.execute(
                """
                INSERT INTO ettend_db.public.attendance_proj_staff_conference
                (machine_id, staff_id, staff_name, staff_dept, attendance_score, remarks, 
                 conference_type, conference_category, conference_title, conference_venue, conference_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (staff_id) 
                DO UPDATE SET 
                    staff_name = EXCLUDED.staff_name,
                    staff_dept = EXCLUDED.staff_dept,
                    attendance_score = EXCLUDED.attendance_score,
                    remarks = EXCLUDED.remarks,
                    conference_type = EXCLUDED.conference_type,
                    conference_category = EXCLUDED.conference_category,
                    conference_title = EXCLUDED.conference_title,
                    conference_venue = EXCLUDED.conference_venue,
                    conference_date = EXCLUDED.conference_date
                """,
                (id, staff_id, staff_name, department, staff_score, remark,
                 "conference", "staff", "staff_conference", "staff_conference_venue", conference_date)
            )

        # Commit changes
        conn.commit()
        messages.success(request, "Staff data uploaded and saved successfully.")

    except psycopg2.DatabaseError as error:
        messages.error(request, f"Database Error: {error}")
    finally:
        # Close cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

    # Render the data in the staff_view_upload.html template
    return render(request, 'staff_view_upload.html', {'staff_data': staff_data_dict})


def staff_events_creation(request):
    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        event_venue = request.POST.get('event_venue')
        event_type = request.POST.get('event_type')
        event_category = request.POST.get('event_category')
        form = Upload_staff_events_attendance(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']

            staff_attend = pd.read_excel(file, engine='openpyxl')
            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            # Save the DataFrame to a folder
            filename = f'STAFF_EVENT_ATTENDANCE/staff_event_data{current_date}.csv'
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            staff_attend.to_csv(file_path, index=False)

        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        if conn:
            print("Database connection successful")
        else:
            print("Database connection failed")

        cur = conn.cursor()  # Create cursor once, before the loop

        # Iterate over the staff_attend DataFrame to update the database
        for index, row in staff_attend.iterrows():
            staff_id = str(row['staffid'])  # ✅ Cast staff_id to string
            staff_name = row['Name']
            department = row['dept']
            staff_score = 1
            attendance_status = 1

            print(f"Processing staff ID: {staff_id}")  # Debugging

            if event_type == "conference":
                cur.execute(
                    """
                    UPDATE ettend_db.public.attendance_proj_staff_conference
                    SET staff_dept = %s,
                        conference_title = %s,
                        conference_date = %s,
                        conference_time = %s,
                        conference_venue = %s,
                        conference_category = %s,
                        remarks = %s,
                        attendance_score = %s
                    WHERE staff_id = %s
                    """,
                    (
                        department,
                        event_title,
                        event_date,
                        event_time,
                        event_venue,
                        event_category,
                        "present",
                        attendance_status,
                        staff_id
                    )
                )
                rows_updated = cur.rowcount
                if rows_updated == 0:
                    print(f"No rows updated for staff_id {staff_id}")
                else:
                    print(f"{rows_updated} row(s) updated for staff_id {staff_id}")

        # Commit once after processing all rows
        conn.commit()
        print("Changes committed to the database")

        # Close cursor and connection
        cur.close()
        conn.close()
        print("Connection closed")

        messages.success(request, "Event created successfully")
        staff_event_attendance_generator(request, event_title, event_date)
        return redirect('staff_event_create')
    else:
        form = Upload_staff_events_attendance()

    return render(request, 'staff_create_event.html', {'form': form})


# staff event attendance view
def staff_event_attendance_generator(request, event_title, event_date):
    if isinstance(event_date, str):
        try:
            today = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            today = datetime.strptime(event_date, "%d/%m/%Y").date()
    else:
        today = event_date

    today_format = today.strftime("%d/%m/%Y")




    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        if conn:
            print("Database connection successful")
        else:
            print("Database connection failed")

        # Create a cursor and execute the query
        cur = conn.cursor()

        # Get column names to map the results
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'attendance_proj_staff_conference'"
        )
        column_names = [col[0] for col in cur.fetchall()]

        # Execute the query to fetch all records
        cur.execute("SELECT * FROM ettend_db.public.attendance_proj_staff_conference")
        staff_event_attendance = cur.fetchall()

        if not staff_event_attendance:
            print("No records found in the table.")
            staff_event_attendance = []  # Set to empty list if no records found

        # Convert to a list of dictionaries
        attendance_list = [dict(zip(column_names, row)) for row in staff_event_attendance]

        # Generate QR codes for each staff member in the attendance list
        for staff in attendance_list:
            total_possible_score = 15  # Assuming this is a fixed value
            # Generate QR code containing the staff ID, event type, and today's date
            qr_data = f"AUTH :  | E-TTEND | VERITAS UNIVERSITY ABUJA {event_title} | {today_format}"
            staff['qr_code'] = staff_auth_generate_qr_code(qr_data)
            # TOTAL ROWS IN THE DATABASE
            staff['total_rows'] = len(attendance_list)

        # Close the cursor and connection
        cur.close()
        conn.close()
        print("Connection closed")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return render(request, 'staff_generate_attendance.html', {'error': "Failed to fetch attendance records."})

    # Render the results in the template
    return render(request, 'staff_generate_attendance.html', {'staff_event_attendance': attendance_list})


def staff_auth_generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # Combine data into a string for the QR code

    qr.add_data(data)
    qr.make(fit=True)

    # Create the image in memory
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # Encode the image in base64 and return it as a string
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str









import pandas as pd
import os
import psycopg2
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .forms import Upload_registered_students

# Faculty mapping
faculty_mapping = {
    "BIOLOGICAL SCIENCES": "Natural and Applied Sciences",
    "BIOTECHNOLOGY AND ENVIRONMENTAL BIOLOGY": "Natural and Applied Sciences",
    "BIOCHEMISTRY": "Natural and Applied Sciences",
    "CHEMISTRY": "Natural and Applied Sciences",
    "PURE AND APPLIED CHEMISTRY": "Natural and Applied Sciences",
    "COMPUTER AND INFORMATION TECHNOLOGY": "Natural and Applied Sciences",
    "MATHEMATICS": "Natural and Applied Sciences",
    "MICROBIOLOGY": "Natural and Applied Sciences",
    "SOFTWARE ENGINEERING": "Natural and Applied Sciences",
    "PHYSICS WITH ELECTRONICS": "Natural and Applied Sciences",
    "PURE AND APPLIED PHYSICS": "Natural and Applied Sciences",
    "ACCOUNTING": "Management Sciences",
    "PHARMACY" :"Pharmaceutical Sciences",
    "MEDICINE AND SURGERY": "Health Sciences",
    "MEDICAL LABORATORY SCIENCES": "Health Sciences",
    "MEDICAL SCIENCES": "Health Sciences",
    "PHARMACEUTICAL MICROBIOLOGY AND BIOTECHNOLOGY": "Health Sciences",
    "BANKING AND FINANCE": "Management Sciences",
    "BUSINESS ADMINISTRATION": "Management Sciences",
    "ENTREPRENEURSHIP": "Management Sciences",
    "MANAGEMENT SCIENCES": "Management Sciences",
    "MARKETING": "Management Sciences",
    "ENGLISH AND LITERARY STUDIES": "Humanities",
    "HISTORY AND INTERNATIONAL RELATIONS": "Humanities",
    "PHILOSOPHY": "Humanities",
    "RELIGIOUS STUDIES": "Humanities",
    "HUMANITIES": "Humanities",
    "ECONOMICS": "Social Sciences",
    "THEOLOGY": "Ecclesiastical Theology",
    "SACRED THEOLOGY": "Ecclesiastical Theology",
    "EDUCATIONAL FOUNDATIONS": "Education",
    'BURSARY': 'Non Academic/ Administrative',
    'GES':'Non Academic/ Administrative',
    'ICT UNIT': 'Non Academic/ Administrative',
    'LIBRARY': 'Non Academic/ Administrative',
    'AUDIT': 'Non Academic/ Administrative',
    'MEDICAL CENTRE': 'Non Academic/ Administrative',
    'REGISTRY': 'Non Academic/ Administrative',
    'STUDENTS AFFAIRS': 'Non Academic/ Administrative',
    'PG SCHOOL': 'Non Academic/ Administrative',
    'VICE CHANCELLOR':'Top Administrative',
    "MASS COMMUNICATION": "Social Sciences",
    "POLITICAL SCIENCE AND DIPLOMACY": "Social Sciences",
    "PUBLIC ADMINISTRATION": "Social Sciences",
    "SOCIOLOGY": "Social Sciences",
    "ARTS AND SOCIAL SCIENCE EDUCATION": "Education",
    "EDUCATIONAL FOUNDATION": "Education",
    "SCIENCE EDUCATION": "Education",
    "CIVIL ENGINEERING": "Engineering",
    "RELIGION AND INTERCULTURAL STUDIES": "Education",
    "COMPUTER ENGINEERING": "Engineering",
    "ELECTRICAL AND ELECTRONIC ENGINEERING": "Engineering",
    "ELECTRICAL/ELECTRONIC ENGINEERING": "Engineering",
    "MECHANICAL ENGINEERING": "Engineering",
    "LAW": "Law",
    "NURSING SCIENCES": "Health Sciences",
    "PUBLIC HEALTH": "Health Sciences"
}

@csrf_exempt
def upload_students_records_db(request):
    if request.method == 'POST':
        level = request.POST.get('Level')
        form = Upload_students_database(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, "Invalid form submission.")
            return render(request, 'STUDENTEVENTS/upload_students_records.html', {'form': form})

        try:
            conn = psycopg2.connect(
                dbname='ettend_db',
                user='postgres',
                password='blaze',
                host='localhost',
                port='5432'
            )
            cur = conn.cursor()
        except psycopg2.DatabaseError as e:
            messages.error(request, f"Database connection error: {e}")
            return render(request, 'STUDENTEVENTS/upload_students_records.html', {'form': form})

        if 'file' not in form.cleaned_data:
            messages.error(request, "No file was uploaded.")
            return render(request, 'STUDENTEVENTS/upload_students_records.html', {'form': form})

        try:
            file = form.cleaned_data['file']
            df = pd.read_excel(file, engine='openpyxl')

            # Standardize column names
            df.columns = df.columns.str.strip().str.upper()

            # Column validation
            required_columns = ['FIRSTNAME', 'LASTNAME', 'MATRIC_NO', 'GENDER', 'LEVEL', 'DEPARTMENT']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messages.error(request, f"Missing columns in the uploaded file: {', '.join(missing_columns)}")
                return render(request, 'STUDENTEVENTS/upload_students_records.html', {'form': form})

            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            # Normalize DEPARTMENT column
            df['DEPARTMENT'] = df['DEPARTMENT'].astype(str).str.strip().str.upper()

            # Normalize mapping keys
            faculty_mapping_upper = {k.upper(): v for k, v in faculty_mapping.items()}

            # Add Faculty column
            df['FACULTY'] = df['DEPARTMENT'].map(faculty_mapping_upper)
            file_initials = "student_records"

            # Save updated file with Faculty column
            file_path = save_csv_to_directory(df, 'STUDENTS_DB_RECORDS', file_initials, level, current_date)

            # Insert records into database with Faculty field
            insert_records_with_faculty(df, cur, level)

            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, "File uploaded and processed successfully.")
        except Exception as e:
            messages.error(request, f"Error processing data: {e}")

    form = Upload_registered_students()
    return render(request, 'STUDENTEVENTS/upload_students_records.html', {'form': form})


def save_csv_to_directory(df, save_dir, file_initials, level, current_date):
    """
    Saves the DataFrame with Faculty field to a specified directory.
    """
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{file_initials.lower().replace(' ', '_')}_{level}l_{current_date}.csv"
    file_path = os.path.join(save_dir, filename)
    df.to_csv(file_path, index=False)
    return file_path

def insert_records_with_faculty(df, cursor, level):
    """
    Inserts records into database tables named based on the student level.
    """
    table_name = f"attendance_proj_vua_{level}l_mass_students"
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO ettend_db.public.{table_name} 
        (student_matric_no, student_fname,student_lname,student_gender,student_level,department,
         faculty, week_1,week_2,week_3,week_4,week_5,week_6,week_7,week_8,week_9,week_10,week_11,week_12,
         student_total_attendance_score,student_remarks)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
         ON CONFLICT (student_matric_no) DO NOTHING;
        """
        cursor.execute(insert_query, (
            row['MATRIC_NO'],
            row['FIRSTNAME'],
            row['LASTNAME'],
            row['GENDER'],
            row['LEVEL'],
            row['DEPARTMENT'],
            row['FACULTY'],
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            "pending"


        ))

# view uploaded student records in the db for each level

# View uploaded student records in the database for 100-level Computer Science students
def view_uploaded_student_100_records(request):
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()
        print("Database connection successful.")

        # Query to fetch records for 100-level Computer Science students
        query = """
        SELECT 
            student_fname, student_lname, student_matric_no, student_gender, 
            student_level, department, faculty, week_1, week_2, week_3, week_4, week_5, 
            week_6, week_7, week_8, week_9, week_10, week_11, week_12, 
            student_total_attendance_score, student_remarks
        FROM 
            ettend_db.public.attendance_proj_vua_100l_mass_students;
        """
        cur.execute(query)
        student_records = cur.fetchall()
        print("Student records fetched successfully.")

        # Define column names (map with query result)
        column_names = [
             "student_fname", "student_lname", "student_matric_no", "student_gender",
            "student_level", "department", "faculty", "week_1", "week_2", "week_3", "week_4", "week_5",
            "week_6", "week_7", "week_8", "week_9", "week_10", "week_11", "week_12",
            "student_total_attendance_score", "student_remarks"
        ]

        # Map records to column names
        students = [dict(zip(column_names, record)) for record in student_records]

        cur.close()
        conn.close()
        print("Connection to the database closed.")

    except psycopg2.DatabaseError as error:
        print(f"Error: {error}")
        return render(request, 'STUDENTEVENTS/view_uploaded_100l_student_records.html', {'error': "Failed to fetch student records from the database."})

    # Render the records in the template
    return render(request, 'STUDENTEVENTS/view_uploaded_100l_student_records.html', {'students': students})


import psycopg2
from django.shortcuts import render

def view_uploaded_student_200_records(request):
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()
        print("Database connection successful.")

        # Query to fetch records for 200-level Computer Science students
        query = """
        SELECT 
            student_fname, student_lname, student_matric_no, student_gender, 
            student_level, department, faculty, week_1, week_2, week_3, week_4, week_5, 
            week_6, week_7, week_8, week_9, week_10, week_11, week_12, 
            student_total_attendance_score, student_remarks
        FROM 
            ettend_db.public.attendance_proj_vua_200l_mass_students;
        """
        cur.execute(query)
        student_records = cur.fetchall()
        print("Student records fetched successfully.")

        # Define column names (map with query result)
        column_names = [
             "student_fname", "student_lname", "student_matric_no", "student_gender",
            "student_level", "department", "faculty", "week_1", "week_2", "week_3", "week_4", "week_5",
            "week_6", "week_7", "week_8", "week_9", "week_10", "week_11", "week_12",
            "student_total_attendance_score", "student_remarks"
        ]

        # Map records to column names
        students = [dict(zip(column_names, record)) for record in student_records]

        cur.close()
        conn.close()
        print("Connection to the database closed.")

        # Corrected Return Statement
        return render(request, 'STUDENTEVENTS/view_uploaded_200l_student_records.html', {'students': students})

    except psycopg2.DatabaseError as error:
        print(f"Database Error: {error}")
        return render(request, 'STUDENTEVENTS/view_uploaded_200l_student_records.html', {'error': "Failed to fetch student records from the database."})


import psycopg2
from django.shortcuts import render

def view_uploaded_student_300l_records(request):
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()
        print("Database connection successful.")

        # Query to fetch records for 300-level Computer Science students
        query = """
        SELECT 
            student_fname, student_lname, student_matric_no, student_gender, 
            student_level, department, faculty, week_1, week_2, week_3, week_4, week_5, 
            week_6, week_7, week_8, week_9, week_10, week_11, week_12, 
            student_total_attendance_score, student_remarks
        FROM 
            ettend_db.public.attendance_proj_vua_300l_mass_students;
        """
        cur.execute(query)
        student_records = cur.fetchall()
        print("Student records fetched successfully.")

        # Define column names (map with query result)
        column_names = [
            "student_fname", "student_lname", "student_matric_no", "student_gender",
            "student_level", "department", "faculty", "week_1", "week_2", "week_3", "week_4", "week_5",
            "week_6", "week_7", "week_8", "week_9", "week_10", "week_11", "week_12",
            "student_total_attendance_score", "student_remarks"
        ]

        # Map records to column names
        students = [dict(zip(column_names, record)) for record in student_records]

        cur.close()
        conn.close()
        print("Connection to the database closed.")

        # Corrected Return Statement
        return render(request, 'STUDENTEVENTS/view_uploaded_300l_student_records.html', {'students': students})

    except psycopg2.DatabaseError as error:
        print(f"Database Error: {error}")
        return render(request, 'STUDENTEVENTS/view_uploaded_300l_student_records.html', {'error': "Failed to fetch student records from the database."})



import psycopg2
from django.shortcuts import render

def view_uploaded_student_400l_records(request):
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()
        print("Database connection successful.")

        # Query to fetch records for 400-level Computer Science students
        query = """
        SELECT 
            student_fname, student_lname, student_matric_no, student_gender, 
            student_level, department, faculty, week_1, week_2, week_3, week_4, week_5, 
            week_6, week_7, week_8, week_9, week_10, week_11, week_12, 
            student_total_attendance_score, student_remarks
        FROM 
            ettend_db.public.attendance_proj_vua_400l_mass_students;
        """
        cur.execute(query)
        student_records = cur.fetchall()
        print("Student records fetched successfully.")

        # Define column names (map with query result)
        column_names = [
            "student_fname", "student_lname", "student_matric_no", "student_gender",
            "student_level", "department", "faculty", "week_1", "week_2", "week_3", "week_4", "week_5",
            "week_6", "week_7", "week_8", "week_9", "week_10", "week_11", "week_12",
            "student_total_attendance_score", "student_remarks"
        ]

        # Map records to column names
        students = [dict(zip(column_names, record)) for record in student_records]

        cur.close()
        conn.close()
        print("Connection to the database closed.")

        # Corrected Return Statement
        return render(request, 'STUDENTEVENTS/view_uploaded_400l_student_records.html', {'students': students})

    except psycopg2.DatabaseError as error:
        print(f"Database Error: {error}")
        return render(request, 'STUDENTEVENTS/view_uploaded_400l_student_records.html',
                      {'error': "Failed to fetch student records from the database."})



# create mass attendance


from datetime import datetime
import pandas as pd
import psycopg2
import os
from zipfile import BadZipFile
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from .forms import Upload_students_events_attendance

from django.shortcuts import render
from django.contrib import messages
import pandas as pd
import psycopg2
from datetime import datetime
import os
from zipfile import BadZipFile
from django.conf import settings
from .forms import Upload_students_events_attendance

def student_mass_attendance(request):
    global student_attend, current_date, student_id

    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        event_venue = request.POST.get('event_venue')
        event_type = request.POST.get('event_type')
        event_category = request.POST.get('event_category')

        # Handle week and level conversion safely
        try:
            week = int(request.POST.get('week', 0))
            level = int(request.POST.get('level', 0))
            if level == 0:
                raise ValueError("Level must be specified.")
        except ValueError:
            messages.error(request, "Week and level must be valid integers greater than zero.")
            return render(request, 'STUDENTEVENTS/create_mass_attendance.html')

        form = Upload_students_events_attendance(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']
            try:
                if file.name.endswith('.csv'):
                    student_attend = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    student_attend = pd.read_excel(file, engine='openpyxl')
                elif file.name.endswith('.xls'):
                    student_attend = pd.read_excel(file, engine='xlrd')
                else:
                    messages.error(request, "Unsupported file format. Please upload a valid .xlsx or .csv file.")
                    return render(request, 'STUDENTEVENTS/create_mass_attendance.html', {'form': form})
            except (BadZipFile, ValueError) as e:
                messages.error(request, f"Error reading file: {str(e)}")
                return render(request, 'STUDENTEVENTS/create_mass_attendance.html', {'form': form})

            # Save uploaded data as CSV
            current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f'STUDENT_MASS_ATTENDANCE/student_event_data_{current_date}.csv'
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            student_attend.to_csv(file_path, index=False)

            # Database connection
            try:
                conn = psycopg2.connect(
                    dbname='ettend_db',
                    user='postgres',
                    password='blaze',
                    host='localhost',
                    port='5432'
                )
                cur = conn.cursor()
            except Exception as e:
                messages.error(request, f"Database connection error: {str(e)}")
                return render(request, 'STUDENTEVENTS/create_mass_attendance.html', {'form': form})

            # Iterate through DataFrame rows
            for index, row in student_attend.iterrows():
                student_id = str(row['ID']).strip()[-4:]  # Ensures correct student ID format
                student_name = row['Name']

                attendance_status = 1

                print(f"Processing student ID: {student_id}")

                if event_type == "mass":
                    table_name = f"attendance_proj_vua_{level}l_mass_students"
                    week_column = f'week_{week}'

                    # Corrected SQL query using RIGHT() for last 4 characters
                    insert_query = f"""
                        UPDATE ettend_db.public.{table_name} 
                        SET {week_column} = %s
                        WHERE RIGHT(student_matric_no, 4) = %s;
                    """
                    try:
                        cur.execute(insert_query, (attendance_status, student_id))
                    except Exception as e:
                        print(f"Error updating student {student_id}: {str(e)}")

            # Commit and close database connection
            conn.commit()
            cur.close()
            conn.close()

            messages.success(request, "Event created successfully")
            return render(request, 'STUDENTEVENTS/create_mass_attendance.html', {'form': form})

    else:
        form = Upload_students_events_attendance()

    return render(request, 'STUDENTEVENTS/create_mass_attendance.html', {'form': form})

# student event attendance view
import psycopg2
from django.shortcuts import render
from datetime import date
import qrcode
import base64
from io import BytesIO

from django.shortcuts import redirect

def student_mass_attendance_generator(request):
    global event_title, event_date, level
    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        event_venue = request.POST.get('event_venue')
        event_type = request.POST.get('event_type')
        event_category = request.POST.get('event_category')

        # Ensure 'week' and 'level' are properly converted to integers
        try:
            week = int(request.POST.get('week', 0))
            level = int(request.POST.get('level', 0))
        except ValueError:
            messages.error(request, "Week and level must be integers.")
            return render(request, 'STUDENTEVENTS/view_mass_attendance.html',
                          {'error': 'Invalid level or week value provided.'})

    today = date.today().strftime("%d/%m/%Y")

    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        print("Database connection successful")

        # Create a cursor and execute the query
        cur = conn.cursor()

        # Corrected string formatting in table name
        table_name = f"attendance_proj_vua_{level}l_mass_students"

        # Get column names for mapping the results
        cur.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,)
        )
        column_names = [col[0] for col in cur.fetchall()]

        # Fetch student attendance records
        cur.execute(f"SELECT * FROM {table_name}")
        student_event_attendance = cur.fetchall()

        if not student_event_attendance:
            print("No records found in the table.")
            student_event_attendance = []

        # Convert to list of dictionaries for easy template rendering
        attendance_list = [dict(zip(column_names, row)) for row in student_event_attendance]

        # Generate QR codes for each student in the attendance list
        for student in attendance_list:
            total_possible_score = 15
            qr_data = f"AUTH: | E-TTEND | VERITAS UNIVERSITY ABUJA | {event_title} | {event_date} | ID: {student.get('student_id', 'N/A')}"
            student['qr_code'] = student_auth_generate_qr_code(qr_data)
            student['total_rows'] = len(attendance_list)

        # Store data in session to pass it to another view
        request.session['attendance_data'] = attendance_list
        request.session['event_title'] = event_title
        request.session['event_date'] = event_date
        request.session['level'] = level

        # Close connections
        cur.close()
        conn.close()
        print("Connection closed")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return render(request, 'STUDENTEVENTS/generate_student_massattendance_form.html',
                      {'error': "Failed to fetch attendance records."})

    # Redirect to the new template FOR DIFFERENT LEVEL
    return redirect(f'view_student_mass_attendance_level_{level}')
    



def view_mass_attendance_records(request):
    attendance_data = request.session.get('attendance_data', [])
    event_title = request.session.get('event_title', 'N/A')
    event_date = request.session.get('event_date', 'N/A')
    level = request.session.get('level', 0)

    if not attendance_data:
        messages.warning(request, "No attendance data available.")
        return redirect('view_student_mass_attendance')

    return render(request, 'STUDENTEVENTS/view_mass_attendance.html', {
        'student_event_attendance': attendance_data,
        'event_title': event_title,
        'event_date': event_date,
           'level': level
    })

import qrcode
import base64
from io import BytesIO
# QR Code Generation Function
import qrcode
import base64
from io import BytesIO
from qrcode.main import QRCode


def student_auth_generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create the image in memory
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # Encode the image in base64 and return it as a string
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str


def student_mass_absenteeism_generator(request):
    global event_title, event_date, level, week

    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        event_venue = request.POST.get('event_venue')
        event_type = request.POST.get('event_type')
        event_category = request.POST.get('event_category')

        # Ensure 'week' and 'level' are properly converted to integers
        try:
            week = int(request.POST.get('week', 0))
            level = int(request.POST.get('level', 0))
        except ValueError:
            messages.error(request, "Week and level must be integers.")
            return render(request, 'STUDENTEVENTS/student_absent_mass.html',
                          {'error': 'Invalid level or week value provided.'})

    today = date.today().strftime("%d/%m/%Y")

    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        print("Database connection successful")

        # Create a cursor and execute the query
        cur = conn.cursor()

        # Corrected string formatting in table name
        table_name = f"attendance_proj_vua_{level}l_mass_students"

        # Get column names for mapping the results
        cur.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,)
        )
        column_names = [col[0] for col in cur.fetchall()]

        # Fetch student attendance records
        cur.execute(f"SELECT * FROM {table_name}")
        student_event_attendance = cur.fetchall()

        if not student_event_attendance:
            print("No records found in the table.")
            student_event_attendance = []

        # Convert to list of dictionaries for easy template rendering
        attendance_list = [dict(zip(column_names, row)) for row in student_event_attendance]

        # Filter only records where all 'week' values are zero
        filtered_attendance_list = [
            student for student in attendance_list
            if all(value == 0 for key, value in student.items() if 'week' in key)
        ]

        # Calculate total score and generate QR codes
        for student in filtered_attendance_list:
            filtered_weeks = {week: value for week, value in student.items() if 'week' in week and value == 0}
            student['filtered_total_score'] = sum(filtered_weeks.values())

            # ANALYSIS OF FILTERED DATA ... GET TOTAL ABSENT STUDENT BY DEPARTMENT, FACULTY, GENDER
            total_absent_by_department = {}
            total_absent_by_faculty = {}
            total_absent_by_gender = {}

            for student in filtered_attendance_list:
                # Count by department
                department = student.get('department', 'Unknown')
                total_absent_by_department[department] = total_absent_by_department.get(department, 0) + 1

                # Count by faculty
                faculty = student.get('faculty', 'Unknown')
                total_absent_by_faculty[faculty] = total_absent_by_faculty.get(faculty, 0) + 1

                # Count by gender
                gender = student.get('student_gender', 'Unknown')
                total_absent_by_gender[gender] = total_absent_by_gender.get(gender, 0) + 1

            # Attach analysis results to session or pass to context
            request.session['total_absent_by_department'] = total_absent_by_department
            request.session['total_absent_by_faculty'] = total_absent_by_faculty
            request.session['total_absent_by_gender'] = total_absent_by_gender
            request.session['week'] = week





        # Store data in session to pass it to another view
        request.session['attendance_data'] = filtered_attendance_list
        request.session['event_title'] = event_title
        request.session['event_date'] = event_date
        request.session['level'] = level
        request.session['week']= week

        # Close connections
        cur.close()
        conn.close()
        print("Connection closed")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return render(request, 'STUDENTEVENTS/student_absent_mass.html',
                      {'error': "Failed to fetch attendance records."})

    # Redirect to the new template
    return redirect('view_student_mass_absenteeism')


from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date
import psycopg2



def view_student_absenteeism_records(request):
    attendance_data = request.session.get('attendance_data', [])
    event_title = request.session.get('event_title', 'N/A')
    event_date = request.session.get('event_date', 'N/A')
    level = request.session.get('level', 0)
    week = request.session.get('week', 0)

    if not attendance_data:
        messages.warning(request, "No attendance data available.")
        return redirect('view_student_mass_absenteeism')

    qr_data = f"AUTH: | E-TTEND | VERITAS UNIVERSITY ABUJA | {event_title} | {event_date} | "
    qr_gen= student_auth_generate_qr_code(qr_data)


    return render(request, 'STUDENTEVENTS/view_student_absenteeism_records.html', {
        'student_event_attendance': attendance_data,
        'event_title': event_title,
        'event_date': event_date,
        'level': level,
        'week': week,
        'student_qr_code': qr_gen,
    })

# STAFF ATTENDANCE PROCESSING
# STAFF ATTENDANCE PROCESSING USING Staff_mass_attendance MODEL
def insert_staff_records(df, cursor):
    for _, row in df.iterrows():

        staff_id = (
            str(row.get('STAFF_NO')).strip()
            if pd.notna(row.get('STAFF_NO')) else None
        )

        first_name = str(row.get('FIRSTNAME')).strip()
        last_name = str(row.get('LASTNAME')).strip()
        title = str(row.get('TITLE')).strip()
        gender = str(row.get('GENDER')).strip()
        department = str(row.get('DEPARTMENT')).strip()
        staff_type = str(row.get('STAFF_TYPE')).strip()

        # ✅ RFID (CRITICAL FIX)
        staff_rfid = (
            str(row.get('RFID')).strip()
            if pd.notna(row.get('RFID')) else None
        )

        staff_name = f"{title} {first_name} {last_name}"

        cursor.execute(
            """
            INSERT INTO attendance_proj_staff_mass_records
            (
                staff_id,
                staff_fname,
                staff_gender,
                department,
                staff_category,
                staff_rfid
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (staff_id) DO UPDATE
            SET
                staff_fname = EXCLUDED.staff_fname,
                staff_gender = EXCLUDED.staff_gender,
                department = EXCLUDED.department,
                staff_category = EXCLUDED.staff_category,
                staff_rfid = EXCLUDED.staff_rfid
            """,
            (
                staff_id,
                staff_name,
                gender,
                department,
                staff_type,
                staff_rfid
            )
        )

def upload_staff_records_db(request):
    if request.method == 'POST':
        form = Upload_staff_records(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, "Invalid form submission.")
            return render(request, 'STAFFEVENTS/upload_staff_records.html', {'form': form})

        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                dbname='ettend_db',
                user='postgres',
                password='blaze',
                host='localhost',
                port='5432'
            )
            cur = conn.cursor()
        except psycopg2.DatabaseError as e:
            messages.error(request, f"Database connection error: {e}")
            return render(request, 'STAFFEVENTS/upload_staff_records.html', {'form': form})

        try:
            file = form.cleaned_data['file']
            df = pd.read_excel(file, engine='openpyxl')

            # Clean up column names
            df.columns = (
                df.columns.str.strip()
                .str.upper()
                .str.replace(" ", "_")
            )

            # Detect S/NO column
            sno_column = None
            for col in df.columns:
                if col in ["S/NO", "S_NO", "S.NO", "SNO"]:
                    sno_column = col
                    break

            if sno_column is None:
                messages.error(request, "S/NO column not found.")
                return render(request, 'STAFFEVENTS/upload_staff_records.html', {'form': form})

            # Default week values: 12 weeks
            week_defaults = [0] * 12  # week_1 → week_12

            rows_processed = 0
            rows_skipped = 0

            # Determine RFID column name in Excel (adjust if necessary)
            rfid_col = 'RFID'
            if rfid_col not in df.columns:
                rfid_col = None  # if column doesn't exist, all RFID will be None

            for idx, row in df.iterrows():
                # Determine staff_id
                raw_staff_no = row.get('STAFF_NO')
                raw_sno = row.get(sno_column)

                if pd.notna(raw_staff_no) and str(raw_staff_no).strip() not in ["", "--"]:
                    staff_id = str(raw_staff_no).strip()
                elif pd.notna(raw_sno):
                    staff_id = str(int(raw_sno))
                else:
                    rows_skipped += 1
                    continue  # skip rows without staff ID

                # Extract other fields with defaults
                staff_title = str(row.get('TITLE', '')).strip() or "N/A"
                fname = str(row.get('FIRSTNAME', '')).strip() or "N/A"
                lname = str(row.get('LASTNAME', '')).strip() or "N/A"
                gender = str(row.get('GENDER', '')).strip() or "UNKNOWN"
                department = str(row.get('DEPARTMENT', '')).strip() or "UNKNOWN"
                staff_category = str(row.get('STAFF_TYPE', '')).strip() or "UNKNOWN"
                faculty = faculty_mapping.get(department, "UNKNOWN")
                staff_total_attendance_score = 0

                # Process RFID safely
                if rfid_col:
                    raw_rfid = row.get(rfid_col)
                    if pd.notna(raw_rfid):
                        if isinstance(raw_rfid, float):
                            staff_rfid = str(int(raw_rfid))
                        else:
                            staff_rfid = str(raw_rfid).strip()
                    else:
                        staff_rfid = None
                else:
                    staff_rfid = None

                # Insert or update staff record
                cur.execute("""
                    INSERT INTO attendance_proj_staff_mass_records (
                        staff_id,
                        staff_title,
                        staff_fname,
                        staff_lname,
                        staff_gender,
                        department,
                        faculty,
                        staff_category,
                        staff_total_attendance_score,
                        week_1, week_2, week_3, week_4, week_5,
                        week_6, week_7, week_8, week_9, week_10,
                        week_11, week_12,
                        staff_rfid
                    ) VALUES (
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s
                    )
                    ON CONFLICT (staff_id) DO UPDATE SET
                        staff_title = EXCLUDED.staff_title,
                        staff_fname = EXCLUDED.staff_fname,
                        staff_lname = EXCLUDED.staff_lname,
                        staff_gender = EXCLUDED.staff_gender,
                        department = EXCLUDED.department,
                        faculty = EXCLUDED.faculty,
                        staff_category = EXCLUDED.staff_category,
                        staff_total_attendance_score = EXCLUDED.staff_total_attendance_score,
                        week_1 = EXCLUDED.week_1,
                        week_2 = EXCLUDED.week_2,
                        week_3 = EXCLUDED.week_3,
                        week_4 = EXCLUDED.week_4,
                        week_5 = EXCLUDED.week_5,
                        week_6 = EXCLUDED.week_6,
                        week_7 = EXCLUDED.week_7,
                        week_8 = EXCLUDED.week_8,
                        week_9 = EXCLUDED.week_9,
                        week_10 = EXCLUDED.week_10,
                        week_11 = EXCLUDED.week_11,
                        week_12 = EXCLUDED.week_12,
                        staff_rfid = EXCLUDED.staff_rfid
                """, (
                    staff_id,
                    staff_title,
                    fname,
                    lname,
                    gender,
                    department,
                    faculty,
                    staff_category,
                    staff_total_attendance_score,
                    *week_defaults,  # 12 zeros for weeks
                    staff_rfid        # RFID last
                ))

                rows_processed += 1

            conn.commit()
            cur.close()
            conn.close()

            messages.success(request, f"Staff records uploaded successfully. Processed: {rows_processed}, Skipped: {rows_skipped}")

        except Exception as e:
            conn.rollback()
            messages.error(request, f"Error processing data: {e}")

    else:
        form = Upload_staff_records()

    return render(request, 'STAFFEVENTS/upload_staff_records.html', {'form': form})



from django.shortcuts import render
import psycopg2

from datetime import datetime


from datetime import datetime
import psycopg2
from django.shortcuts import render

def view_uploaded_staff_records_mass(request):
    try:
        # Connect to the database
        with psycopg2.connect(
                dbname='ettend_db',
                user='postgres',
                password='blaze',
                host='localhost',
                port='5432'
        ) as conn:
            with conn.cursor() as cur:
                print("Database connection successful.")

                # SQL query to fetch staff records
                query = """
                SELECT 
                    staff_id, staff_fname, staff_lname, staff_gender, 
                    staff_title, department, faculty, staff_rfid,
                    week_1, week_2, 
                    week_3, week_4, 
                    week_5, week_6,
                    week_7, week_8,
                    week_9, week_10,
                    week_11, week_12,
                    staff_total_attendance_score, staff_remarks
                FROM 
                    ettend_db.public.attendance_proj_staff_mass_records;
                """
                cur.execute(query)
                staff_records = cur.fetchall()
                print("Staff records fetched successfully.")

        # Correct column names matching SQL query
        column_names = [
            "staff_id", "staff_fname", "staff_lname", "staff_gender",
            "staff_title", "staff_department", "staff_faculty",
            "staff_rfid",  # <-- fixed position
            "week_1", "week_2",
            "week_3", "week_4",
            "week_5", "week_6",
            "week_7", "week_8",
            "week_9", "week_10",
            "week_11", "week_12",
            "staff_total_attendance_score", "staff_remarks"
        ]

        # Map records to column names and format datetime objects
        veritas_staff = []
        for record in staff_records:
            staff_entry = dict(zip(column_names, record))

            # Format datetime fields as strings
            for key, value in staff_entry.items():
                if isinstance(value, datetime):
                    staff_entry[key] = value.strftime('%Y-%m-%d %H:%M:%S')  # Example: 2025-03-26 11:29:57

            veritas_staff.append(staff_entry)

        # Return Staff Records to Template
        return render(request, 'STAFFEVENTS/view_uploaded_staff_records.html', {'veritas_staff': veritas_staff})

    except psycopg2.DatabaseError as error:
        print(f"Database Error: {error}")
        return render(request, 'STAFFEVENTS/view_uploaded_staff_records.html',
                      {'error': "Failed to fetch staff records from the database."})



import pandas as pd
from zipfile import BadZipFile
import os
import psycopg2
from django.conf import settings
from datetime import datetime

import pandas as pd
import os
from datetime import datetime
import psycopg2
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from zipfile import BadZipFile


import os
import re
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import Upload_staff_events_attendance
from .models import staff_Conference  # replace with your DB model
from fuzzywuzzy import fuzz  # optional for name similarity

from rapidfuzz import fuzz, process
import re
from django.db.models import Q

# --------------------------------------------------
# Normalize staff ID (digits only)
# --------------------------------------------------
def normalize_id(staff_id):
    staff_id = str(staff_id or "").strip().upper()
    digits = re.sub(r"\D", "", staff_id)
    print(f"[normalize_id] raw='{staff_id}' → digits='{digits}'")
    return digits


# --------------------------------------------------
# Build DB lookup: map FULL ID + LAST 4 + LAST 3
# --------------------------------------------------
def build_db_lookup():
    lookup_full = {}
    lookup_last4 = {}
    lookup_last3 = {}

    db_records = staff_Conference.objects.all()

    for obj in db_records:
        norm = normalize_id(obj.staff_id)
        if not norm:
            continue

        # Full ID
        lookup_full[norm] = obj
        print(f"[DB FULL LOOKUP] {norm} → {obj.staff_id}")

        # Last 4
        if len(norm) >= 4:
            last4 = norm[-4:]
            lookup_last4.setdefault(last4, []).append(obj)
            print(f"[DB LAST4] {last4} → {obj.staff_id}")

        # Last 3
        if len(norm) >= 3:
            last3 = norm[-3:]
            lookup_last3.setdefault(last3, []).append(obj)
            print(f"[DB LAST3] {last3} → {obj.staff_id}")

    print(f"LOOKUP SIZES → Full={len(lookup_full)}, Last4={len(lookup_last4)}, Last3={len(lookup_last3)}")

    return lookup_full, lookup_last4, lookup_last3


# --------------------------------------------------
# Extended Name Matching
# --------------------------------------------------
def fuzzy_name_matching(uploaded_name, db_objects):
    uploaded_name = (uploaded_name or "").strip().lower()

    if not uploaded_name:
        return None

    # Split first + last name
    parts = uploaded_name.split()
    if len(parts) >= 2:
        uploaded_first = parts[0]
        uploaded_last = parts[-1]
    else:
        uploaded_first = uploaded_name
        uploaded_last = uploaded_name

    best_obj = None
    best_score = 0

    for obj in db_objects:
        db_name = (obj.staff_name or "").lower()

        # Compute scores
        score_full = fuzz.ratio(uploaded_name, db_name)
        score_first = fuzz.partial_ratio(uploaded_first, db_name)
        score_last = fuzz.partial_ratio(uploaded_last, db_name)

        # Weighted total score
        total_score = (score_full * 0.5) + (score_first * 0.25) + (score_last * 0.25)

        print(f"[NAME MATCH] uploaded='{uploaded_name}' vs db='{db_name}' "
              f"(full={score_full}, first={score_first}, last={score_last}, total={total_score})")

        if total_score > best_score:
            best_score = total_score
            best_obj = obj

    if best_score >= 75:  # Confidence threshold
        print(f"✅ BEST NAME MATCH: {best_obj.staff_id} with score={best_score}")
        return best_obj

    print("❌ No strong name match")
    return None


# --------------------------------------------------
# Main Attendance View
# --------------------------------------------------
def staff_mass_attendance(request):
    if request.method != 'POST':
        form = Upload_staff_events_attendance()
        return render(request, 'STAFFEVENTS/create_mass_attendance.html', {'form': form})

    form = Upload_staff_events_attendance(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Invalid form. Please upload a valid file.")
        return redirect("staff_mass_attendance")

    file = form.cleaned_data['file']

    # Load file (unchanged)
    try:
        name = file.name.lower()
        if name.endswith('.csv'):
            df = pd.read_csv(file)
        elif name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file")
    except Exception as e:
        messages.error(request, f"Error reading file: {e}")
        return redirect("staff_mass_attendance")

    # Normalize columns
    df.columns = df.columns.str.strip().str.lower()
    df['id'] = df['id'].astype(str).str.strip()
    df['name'] = df.get('name', df.get('full_name', '')).astype(str).str.strip()

    # Backup file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"STAFF_MASS_ATTENDANCE/staff_upload_{timestamp}.csv"
    backup_path = os.path.join(settings.MEDIA_ROOT, backup_filename)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    df.to_csv(backup_path, index=False)

    # Build lookups
    lookup_full, lookup_last4, lookup_last3 = build_db_lookup()

    updated = 0
    not_found = 0
    unmatched = []

    # Process rows
    for idx, row in df.iterrows():
        raw_id = row['id']
        uploaded_name = row['name']
        norm_id = normalize_id(raw_id)

        match = None

        # 1️⃣ Full ID match
        if norm_id in lookup_full:
            match = lookup_full[norm_id]
            print(f"FULL MATCH → {norm_id} → {match.staff_id}")

        # 2️⃣ Last 4-digit match
        elif len(norm_id) >= 4 and norm_id[-4:] in lookup_last4:
            candidates = lookup_last4[norm_id[-4:]]
            print(f"LAST4 HIT → candidates={len(candidates)}")
            match = fuzzy_name_matching(uploaded_name, candidates)

        # 3️⃣ Last 3-digit match
        elif len(norm_id) >= 3 and norm_id[-3:] in lookup_last3:
            candidates = lookup_last3[norm_id[-3:]]
            print(f"LAST3 HIT → candidates={len(candidates)}")
            match = fuzzy_name_matching(uploaded_name, candidates)

        # 4️⃣ Final name-only fuzzy match
        if not match:
            print(f"FINAL NAME MATCH ATTEMPT → '{uploaded_name}'")
            all_records = staff_Conference.objects.all()
            match = fuzzy_name_matching(uploaded_name, all_records)

        # Save result
        if match:
            match.remarks = "present"
            match.attendance_score = 1
            match.save()
            print(f"✔ UPDATED: {match.staff_id} ({uploaded_name})")
            updated += 1
        else:
            print(f"❌ UNMATCHED → ID='{raw_id}', Name='{uploaded_name}'")
            unmatched.append(row.to_dict())
            not_found += 1

    # Save unmatched
    unmatched_filename = None
    if unmatched:
        unmatched_filename = f"STAFF_MASS_ATTENDANCE/unmatched_{timestamp}.csv"
        unmatched_path = os.path.join(settings.MEDIA_ROOT, unmatched_filename)
        pd.DataFrame(unmatched).to_csv(unmatched_path, index=False)

    messages.success(request,
        f"Updated={updated}, Not found={not_found}, Unmatched File={unmatched_filename}"
    )

    return render(request, 'STAFFEVENTS/create_mass_attendance.html', {'form': form})


import pandas as pd
import os
from datetime import date
import psycopg2
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages


def get_most_recent_csv(folder_path):
    """Fetch the most recent CSV file from the specified folder."""
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the folder.")

    # Sort files by modification time (most recent first)
    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    return os.path.join(folder_path, csv_files[0])


def staff_mass_weekly_attendance_generator(request):
    global event_title, event_date
    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')

    today = date.today().strftime("%d/%m/%Y")

    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        print("Database connection successful")

        # Create a cursor and execute the query
        cur = conn.cursor()

        # Table name for staff attendance
        table_name = "attendance_proj_staff_mass_records"

        # Get column names for mapping the results
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        column_names = [col[0] for col in cur.fetchall()]

        # Fetch staff attendance records
        cur.execute(f"SELECT * FROM {table_name}")
        staff_event_attendance = cur.fetchall()

        if not staff_event_attendance:
            print("No records found in the table.")
            staff_event_attendance = []

        # Convert to list of dictionaries for easy template rendering
        attendance_list = [dict(zip(column_names, row)) for row in staff_event_attendance]

        # === NEW FEATURE: Fetch the most recent CSV file with clock-in times ===
        csv_folder_path = os.path.join(settings.MEDIA_ROOT, 'STAFF_MASS_ATTENDANCE')
        try:
            csv_file_path = get_most_recent_csv(csv_folder_path)
            clockin_data = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            messages.error(request, "No recent clock-in CSV file found.")
            return render(request, 'STAFFEVENTS/view_mass_attendance.html',
                          {'error': 'Recent clock-in CSV file is missing.'})

        # Normalize and clean staff ID data to avoid mismatch
        clockin_data['ID'] = clockin_data['ID'].astype(str).str.strip()

        # Map clock-in times using the exact staff ID
        clockin_dict = dict(zip(clockin_data['ID'], clockin_data['Time']))

        # Append clock-in time directly to the attendance list
        for staff in attendance_list:
            staff_id = str(staff.get('staff_id', '')).strip()  # Clean staff ID
            staff['clockin_time'] = clockin_dict.get(staff_id, 'N/A')  # Match exactly for each staff ID

        # Generate QR codes for each staff member
        for staff in attendance_list:
            total_possible_score = 15
            qr_data = f"AUTH: | E-TTEND | VERITAS UNIVERSITY ABUJA | {event_title} | {event_date} | ID: {staff.get('staff_id', 'N/A')}"
            staff['qr_code'] = staff_auth_generate_qr_code(qr_data)
            staff['total_rows'] = len(attendance_list)

        # Store data in session to pass it to another view
        request.session['attendance_data'] = attendance_list
        request.session['event_title'] = event_title
        request.session['event_date'] = event_date

        # Close connections
        cur.close()
        conn.close()
        print("Connection closed")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return render(request, 'STAFFEVENTS/generate_staff_massattendance_form.html',
                      {'error': "Failed to fetch attendance records."})

    # Redirect to the new template for staff attendance display
    return redirect('view_staff_mass_attendance')


from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Staff

import psycopg2
from django.shortcuts import render, redirect
from django.contrib import messages
import json
def staff_mass_absenteeism_generator(request):
    global event_title, event_date, week, staff, staff_score_weekly

    if request.method == 'POST':
        event_title = request.POST.get('event_title')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        event_venue = request.POST.get('event_venue')
        event_type = request.POST.get('event_type')
        event_category = request.POST.get('event_category')

        try:
            week = int(request.POST.get('week', 0))
        except ValueError:
            messages.error(request, "Week must be an integer.")
            return render(request, 'STAFFEVENTS/staff_absentees.html',
                          {'error': 'Invalid week value provided.'})

    today = date.today().strftime("%d/%m/%Y")

    try:
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        print("Database connection successful")

        cur = conn.cursor()

        table_name = "attendance_proj_staff_mass_records"

        # 🔹 Get column names (must include staff_rfid)
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
        """, (table_name,))
        column_names = [col[0] for col in cur.fetchall()]

        # 🔹 Fetch all records
        cur.execute(f"SELECT * FROM {table_name}")
        staff_event_attendance = cur.fetchall()

        if not staff_event_attendance:
            staff_event_attendance = []

        # 🔹 Convert rows → dict (includes staff_rfid)
        attendance_list = [
            dict(zip(column_names, row))
            for row in staff_event_attendance
        ]

        # 🔹 FILTER: ABSENTEES (ALL WEEK COLUMNS == 0)
        filtered_attendance_list = [
            staff for staff in attendance_list
            if all(
                value == 0
                for key, value in staff.items()
                if key.startswith('week_')
            )
        ]

        # -----------------------------
        # ANALYTICS
        # -----------------------------
        total_absent_by_department = {}
        total_absent_by_role = {}
        total_absent_by_gender = {}

        for staff in filtered_attendance_list:
            department = staff.get('department', 'Unknown')
            role = staff.get('staff_category', 'Unknown')
            gender = staff.get('staff_gender', 'Unknown')

            total_absent_by_department[department] = (
                total_absent_by_department.get(department, 0) + 1
            )
            total_absent_by_role[role] = (
                total_absent_by_role.get(role, 0) + 1
            )
            total_absent_by_gender[gender] = (
                total_absent_by_gender.get(gender, 0) + 1
            )

        # 🔹 WEEK SCORE (RFID SAFE)
        staff_scores_weekly = [
            staff.get(f'week_{week}', 0)
            for staff in filtered_attendance_list
        ]

        # -----------------------------
        # STORE SESSION DATA
        # -----------------------------
        request.session['attendance_data'] = filtered_attendance_list
        request.session['week_score'] = staff_scores_weekly
        request.session['total_absent_by_department'] = total_absent_by_department
        request.session['total_absent_by_role'] = total_absent_by_role
        request.session['total_absent_by_gender'] = total_absent_by_gender
        request.session['event_title'] = event_title
        request.session['event_date'] = event_date
        request.session['week'] = week

        cur.close()
        conn.close()
        print("Connection closed")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return render(request, 'STAFFEVENTS/staff_absentees.html',
                      {'error': "Failed to fetch attendance records."})

    return redirect('view_staff_mass_absenteeism')

def view_staff_absenteeism_records(request):
    attendance_data = request.session.get('attendance_data', [])
    event_title = request.session.get('event_title', 'N/A')
    event_date = request.session.get('event_date', 'N/A')
    week = request.session.get('week', 0)

    if not attendance_data:
        messages.warning(request, "No attendance data available.")
        return redirect('fetch_staff_mass_absentees')

    for staff in attendance_data:
        staff['week_score'] = staff.get(f'week_{week}', 0)
        # ✅ staff['staff_rfid'] is now available in template

    request.session['attendance_data'] = attendance_data

    qr_code_data = (
        f"AUTH | E-TTEND | VERITAS UNIVERSITY | "
        f"{event_title} | {event_date} | STATUS:AUTHENTIC"
    )

    qr_code_image = staff_auth_generate_qr_code_new(qr_code_data)

    return render(request, 'STAFFEVENTS/view_staff_absenteeism.html', {
        'staff_event_attendance': attendance_data,
        'event_title': event_title,
        'event_date': event_date,
        'qr_code': qr_code_image,
        'week': week,
    })


import qrcode
from io import BytesIO
import base64

def staff_auth_generate_qr_code_new(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{qr_base64}"







# STAFF CONFERENNCE / EVENT ATTENDANCE
# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import staff_Conference



# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import staff_Conference


import pandas as pd
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import staff_Conference

# Setup Django logger
logger = logging.getLogger(__name__)
def upload_staff_conference(request):
    def normalize_columns(columns):
        return [col.strip().upper().replace(" ", "_") for col in columns]

    if request.method == "POST":
        if "file" not in request.FILES:
            messages.error(request, "Please select a CSV file to upload.")
            return redirect("upload_staff_conference")

        csv_file = request.FILES["file"]
        logger.info("📂 File received: %s", csv_file.name)

        try:
            df = pd.read_csv(csv_file)
            df.columns = normalize_columns(df.columns)  # Normalize headers
            logger.info("✅ CSV loaded successfully with %d rows", len(df))
            print("✅ CSV Columns:", df.columns.tolist())

            # Required columns
            required_columns = ["FIRSTNAME", "LASTNAME", "STAFF_NO", "GENDER", "DEPARTMENT", "RFID"]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                messages.error(request, f"CSV must contain: {', '.join(required_columns)}")
                logger.error("❌ Missing columns. Found: %s", df.columns.tolist())
                return redirect("upload_staff_conference")

            # Faculty mapping (example, adjust to your school)


            # Add faculty column based on department
            df["FACULTY"] = df["DEPARTMENT"].map(
                lambda d: faculty_mapping.get(str(d).upper().strip(), "Unknown")
            )

            inserted, updated = 0, 0
            for index, row in df.iterrows():
                try:
                    staff_id = str(row["STAFF_NO"]).strip()
                    staff_name = f"{row['FIRSTNAME']} {row['LASTNAME']}".strip()
                    staff_category = str(row.get("STAFF_TYPE", "")).strip()
                    gender = str(row.get("GENDER", "")).strip()
                    title = str(row.get("TITLE", "")).strip()
                    dept = str(row.get("DEPARTMENT", "")).strip()
                    rfid = str(row.get("RFID", "")).strip()
                    faculty = str(row.get("FACULTY", "Administrative")).strip()

                    obj, created = staff_Conference.objects.update_or_create(
                        staff_id=staff_id,
                        defaults={
                            "staff_name": staff_name,
                            "staff_gender": gender,
                            "staff_title": title,
                            "staff_dept": dept,
                            "staff_category": staff_category,
                            "staff_faculty": faculty,
                            "staff_rfid": rfid,
                            "remarks": "Absent",
                            "attendance_score": 0,
                        }
                    )
                    if created:
                        inserted += 1
                        logger.info("🟢 Inserted: %s", staff_name)
                    else:
                        updated += 1
                        logger.info("🟡 Updated: %s", staff_name)

                except Exception as row_error:
                    logger.error("❌ Error processing row %d: %s", index, row_error)

            messages.success(request, f"Upload complete! Inserted {inserted}, Updated {updated}.")
            return redirect("upload_staff_conference")

        except Exception as e:
            logger.exception("❌ Error reading file: %s", e)
            messages.error(request, f"Error processing file: {e}")
            return redirect("upload_staff_conference")

    return render(request, "unscheduled_events.html")


def view_staff_conference(request):
    staff_data = staff_Conference.objects.all()
    return render(request, "view_populated_staff_conf_data.html", {"staff_data": staff_data})



import pandas as pd
import re
import os
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import staff_Conference
from .forms import Upload_staff_events_attendance


# ------------------------------------------------------------
# 🔥 NORMALIZE RFID → Extract only digits
# ------------------------------------------------------------
def normalize_rfid(value):
    if not value:
        return ""

    value = str(value).strip().upper()
    digits = re.sub(r"\D", "", value)
    print(f"normalize_rfid: raw='{value}' → normalized='{digits}'")
    return digits


# ------------------------------------------------------------
# 🔥 BUILD FAST RFID LOOKUP (O(1))
# ------------------------------------------------------------
def build_lookup():
    db_records = staff_Conference.objects.all()
    lookup_map = {}

    for obj in db_records:
        norm = normalize_rfid(obj.staff_rfid)
        if norm:
            if norm in lookup_map:
                print(f"⚠️ Duplicate RFID in DB: {norm}")
            lookup_map[norm] = obj
            print(f"Lookup added: RFID='{norm}' → {obj.staff_name}")

    print(f"Total DB staff records in lookup: {len(lookup_map)}")
    return lookup_map


# ------------------------------------------------------------
# 🔥 MAIN VIEW
# ------------------------------------------------------------
def staff_events_creation_NEW(request):
    if request.method != "POST":
        form = Upload_staff_events_attendance()
        return render(request, "staff_create_event_NEW.html", {"form": form})

    form = Upload_staff_events_attendance(request.POST, request.FILES)

    if not form.is_valid():
        messages.error(request, "Invalid form. Please upload a valid file.")
        return redirect("staff_events_creation_NEW")

    # ------------------------
    # EVENT DETAILS
    # ------------------------
    event_title = request.POST.get("event_title")
    event_date = request.POST.get("event_date")
    event_time = request.POST.get("event_time")
    event_venue = request.POST.get("event_venue")
    event_type = request.POST.get("event_type")
    event_category = request.POST.get("event_category")

    print(
        f"\n➡️ Event: {event_title}, {event_date}, {event_time}, "
        f"{event_venue}, {event_type}, {event_category}"
    )

    file = form.cleaned_data["file"]

    # ------------------------
    # READ EXCEL FILE
    # ------------------------
    try:
        staff_attend = pd.read_excel(file)
        print(
            f"✅ Excel loaded | Rows: {staff_attend.shape[0]} | "
            f"Columns: {staff_attend.shape[1]}"
        )
    except Exception as e:
        messages.error(request, f"Error reading file: {e}")
        return redirect("staff_events_creation_NEW")

    # ------------------------
    # SAVE ORIGINAL FILE
    # ------------------------
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"STAFF_EVENT_ATTENDANCE/staff_event_data_{current_date}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    staff_attend.to_csv(file_path, index=False)

    print(f"✅ Uploaded file saved: {file_path}")

    # ------------------------
    # BUILD RFID LOOKUP
    # ------------------------
    lookup_map = build_lookup()

    # ------------------------
    # PROCESS ROWS
    # ------------------------
    updated = 0
    not_found = 0
    unmatched_rows = []

    for index, row in staff_attend.iterrows():
        raw_rfid = str(
            row.get("RFID")
            or row.get("RFID Number")
            or row.get("Card Number")
            or ""
        ).strip()

        uploaded_name = str(row.get("Name") or "").strip()
        uploaded_dept = str(row.get("Department") or "").strip()

        print(f"\nProcessing row {index}: RFID='{raw_rfid}', Name='{uploaded_name}'")

        norm_uploaded = normalize_rfid(raw_rfid)

        if not norm_uploaded:
            print(f"⚠️ No RFID found at row {index}")
            unmatched_rows.append({
                "row_index": index,
                "uploaded_rfid": raw_rfid,
                "uploaded_name": uploaded_name,
                "reason": "no_rfid",
            })
            not_found += 1
            continue

        matched_obj = lookup_map.get(norm_uploaded)

        if matched_obj:
            print(f"✅ MATCHED RFID: {matched_obj.staff_rfid}")

            if uploaded_name:
                matched_obj.staff_name = uploaded_name
            if uploaded_dept:
                matched_obj.staff_dept = uploaded_dept

            matched_obj.conference_title = event_title
            matched_obj.conference_date = event_date
            matched_obj.conference_time = event_time
            matched_obj.conference_venue = event_venue
            matched_obj.conference_type = event_type
            matched_obj.conference_category = event_category
            matched_obj.remarks = "present"
            matched_obj.attendance_score = 1

            matched_obj.save()
            updated += 1
        else:
            print(f"❌ RFID NOT FOUND: {raw_rfid}")
            unmatched_rows.append({
                "row_index": index,
                "uploaded_rfid": raw_rfid,
                "uploaded_name": uploaded_name,
                "reason": "no_match",
            })
            not_found += 1

    # ------------------------
    # EXPORT UNMATCHED RFIDs
    # ------------------------
    if unmatched_rows:
        unmatched_filename = f"STAFF_EVENT_ATTENDANCE/unmatched_{current_date}.csv"
        unmatched_path = os.path.join(settings.MEDIA_ROOT, unmatched_filename)
        pd.DataFrame(unmatched_rows).to_csv(unmatched_path, index=False)
        print(f"✅ Unmatched RFIDs exported: {unmatched_path}")
    else:
        unmatched_filename = "None"
        print("✅ All RFIDs matched successfully")

    print(
        f"\n✅ Finished | Updated: {updated} | "
        f"Not Found: {not_found} | Total: {staff_attend.shape[0]}"
    )

    messages.success(
        request,
        f"Event created successfully! "
        f"Updated {updated} staff, {not_found} not found. "
        f"Unmatched CSV: {unmatched_filename}"
    )

    return staff_event_attendance_generator_NEW(
        request,
        event_title,
        event_date,
        event_venue,
        event_time,
        staff_attend.shape[0],
    )




# ================================
# Staff Event Attendance Generator
# ================================
def staff_event_attendance_generator_NEW(request, event_title, event_date,event_venue,event_time,total_participant):
    if isinstance(event_date, str):
        try:
            today = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            today = datetime.strptime(event_date, "%d/%m/%Y").date()
    else:
        today = event_date

    today_format = today

    try:
        conn = psycopg2.connect(
            dbname='ettend_db',
            user='postgres',
            password='blaze',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()
        print("✅ Connected to database for fetching attendance")

        # ✅ Fetch all updated records with column aliases
        cur.execute("""
            SELECT 
                staff_id,
                COALESCE(staff_name) AS staff_name,
                COALESCE(staff_dept) AS staff_dept,
                staff_faculty,
                staff_title,
                conference_title,
                conference_date,
                conference_time,
                conference_venue,
                conference_category,
                remarks,
                attendance_score
            FROM attendance_proj_staff_conference
        """)
        column_names = [desc[0] for desc in cur.description]
        staff_event_attendance = cur.fetchall()

        if not staff_event_attendance:
            print("⚠️ No staff records found")
            staff_event_attendance = []

        # ✅ Convert to dictionary
        attendance_list = [dict(zip(column_names, row)) for row in staff_event_attendance]

        # ✅ Add QR codes
        for staff in attendance_list:
            qr_data = f"AUTH : | E-TTEND | VERITAS UNIVERSITY ABUJA. {event_title} | {today_format}"
            staff['qr_code'] = staff_auth_generate_qr_code(qr_data)
            staff['total_rows'] = total_participant

        cur.close()
        conn.close()
        print("✅ Attendance list prepared successfully")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"❌ Error: {error}")
        return render(request, 'staff_generate_attendance.html', {'error': "Failed to fetch attendance records."})

    return render(request, 'staff_generate_attendance.html', {
        'staff_event_attendance': attendance_list,


        'event_date': event_date,
        'event_time': event_time,
        'event_venue': event_venue,
        'event_title': event_title,
        'total_participant': total_participant,
    })


import psycopg2
from django.shortcuts import render
from django.contrib import messages
def add_student(request):
    if request.method == "POST":
        # Get and strip fields
        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        gender = request.POST.get("gender", "").strip()
        department = request.POST.get("department", "").strip()
        level = request.POST.get("level", "").strip()
        matric_no = request.POST.get("matric_no", "").strip()

        # Check missing fields
        missing_fields = []
        if not firstname:
            missing_fields.append("First Name")
        if not lastname:
            missing_fields.append("Last Name")
        if not gender:
            missing_fields.append("Gender")
        if not department:
            missing_fields.append("Department")
        if not level:
            missing_fields.append("Level")
        if not matric_no:
            missing_fields.append("Matric Number")

        if missing_fields:
            messages.error(
                request,
                f"Missing field(s): {', '.join(missing_fields)}"
            )
            return render(request, "add_new_students.html")

        # ------------------------------------
        # MAP LEVEL → TABLE NAME
        # ------------------------------------
        level_table_mapping = {
            "100": "attendance_proj_vua_100l_mass_students",
            "200": "attendance_proj_vua_200l_mass_students",
            "300": "attendance_proj_vua_300l_mass_students",
            "400": "attendance_proj_vua_400l_mass_students",
            "500": "attendance_proj_vua_400l_mass_students",
            "600": "attendance_proj_vua_400l_mass_students"
        }

        table_name = level_table_mapping.get(level)
        if not table_name:
            messages.error(request, "Invalid level selected.")
            return render(request, "add_new_students.html")

        # ------------------------------------
        # FACULTY MAPPING
        # ------------------------------------
        faculty = faculty_mapping.get(department, "UNKNOWN")

        # ------------------------------------
        # DEFAULT WEEK VALUES
        # ------------------------------------
        weeks = [0] * 12  # week_1 → week_12
        total_attendance = 0
        remarks = ""

        try:
            conn = psycopg2.connect(
                dbname="ettend_db",
                user="postgres",
                password="blaze",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # INSERT STUDENT
            cur.execute(
                f"""
                INSERT INTO {table_name} (
                    student_fname,
                    student_lname,
                    student_matric_no,
                    student_gender,
                    department,
                    faculty,
                    student_level,
                    week_1, week_2, week_3, week_4, week_5, week_6,
                    week_7, week_8, week_9, week_10, week_11, week_12,
                    student_total_attendance_score,
                    student_remarks
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s
                )
                """,
                (
                    firstname,
                    lastname,
                    matric_no,
                    gender,
                    department,
                    faculty,
                    level,
                    *weeks,
                    total_attendance,
                    remarks
                )
            )

            conn.commit()
            cur.close()
            conn.close()

            messages.success(
                request,
                f"Student added successfully to {level} level ({department})"
            )

        except Exception as e:
            messages.error(request, f"Error saving student: {e}")

    return render(request, "add_new_students.html")


from django.shortcuts import render
from django.contrib import messages
import psycopg2

def delete_students(request):
    if request.method == "POST":
        level = request.POST.get("level", "").strip()
        matric_numbers = request.POST.get("matric_numbers", "").strip()

        # Validate
        missing_fields = []
        if not level:
            missing_fields.append("Level")
        if not matric_numbers:
            missing_fields.append("Matric Numbers")

        if missing_fields:
            messages.error(request, f"Missing field(s): {', '.join(missing_fields)}")
            return render(request, "delete_students.html")

        # Split by comma and strip spaces
        matric_list = [m.strip() for m in matric_numbers.split(",") if m.strip()]
        if not matric_list:
            messages.error(request, "No valid matric numbers provided.")
            return render(request, "delete_students.html")

        # Map level to table
        level_table_mapping = {
            "100": "attendance_proj_vua_100l_mass_students",
            "200": "attendance_proj_vua_200l_mass_students",
            "300": "attendance_proj_vua_300l_mass_students",
            "400": "attendance_proj_vua_400l_mass_students",
            "500": "attendance_proj_vua_400l_mass_students",
            "600": "attendance_proj_vua_400l_mass_students"
        }
        table_name = level_table_mapping.get(level)
        if not table_name:
            messages.error(request, "Invalid level selected.")
            return render(request, "delete_students.html")

        try:
            conn = psycopg2.connect(
                dbname="ettend_db",
                user="postgres",
                password="blaze",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Build placeholders for IN clause
            placeholders = ','.join(['%s'] * len(matric_list))
            query = f"DELETE FROM {table_name} WHERE student_matric_no IN ({placeholders})"

            cur.execute(query, tuple(matric_list))
            deleted_count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            messages.success(request, f"Deleted {deleted_count} student(s) from level {level}.")

        except Exception as e:
            messages.error(request, f"Error deleting students: {e}")

    return render(request, "delete_students.html")

