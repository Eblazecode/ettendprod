


import pandas as pd
import os
import psycopg2
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .forms import Upload_registered_students, Upload_students_database

# Faculty mapping
faculty_mapping = {
    "BIOLOGICAL SCIENCES": "Natural and Applied Sciences",
    "BIOCHEMISTRY": "Natural and Applied Sciences",
    "CHEMISTRY": "Natural and Applied Sciences",
    "COMPUTER AND INFORMATION TECHNOLOGY": "Natural and Applied Sciences",
    "MATHEMATICS": "Natural and Applied Sciences",
    "MICROBIOLOGY": "Natural and Applied Sciences",
    "SOFTWARE ENGINEERING": "Natural and Applied Sciences",
    "PHYSICS WITH ELECTRONICS": "Natural and Applied Sciences",
    "ACCOUNTING": "Management Sciences",
    "PHARMACY" :"Pharmaceutical Sciences",
    "MEDICINE AND SURGERY": "Health Sciences",
    "MEDICAL LABORATORY SCIENCES": "Health Sciences",
    "BANKING AND FINANCE": "Management Sciences",
    "BUSINESS ADMINISTRATION": "Management Sciences",
    "ENTREPRENEURSHIP": "Management Sciences",
    "MARKETING": "Management Sciences",
    "ENGLISH AND LITERARY STUDIES": "Humanities",
    "HISTORY AND INTERNATIONAL RELATIONS": "Humanities",
    "PHILOSOPHY": "Humanities",
    "RELIGIOUS STUDIES": "Humanities",
    "ECONOMICS": "Social Sciences",
    "THEOLOGY": "Ecclesiastical Theology",
    "SACRED THEOLOGY": "Ecclesiastical Theology",
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
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "Engineering",
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

            # Add Faculty column
            df['FACULTY'] = df['DEPARTMENT'].map(faculty_mapping)
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