from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import csv
import os


# Create your models here.
class Student(models.Model):
    student_id = models.CharField(max_length=10)
    student_name = models.CharField(max_length=50)
    student_email = models.EmailField(max_length=50)
    student_dept = models.CharField(max_length=50)
    student_course = models.CharField(max_length=10)
    student_address = models.CharField(max_length=100)
    student_dob = models.DateField()
    student = models.Manager()


class Attendance(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10)
    attendance = models.Manager()


class Machine(models.Model):
    machine_id = models.CharField(max_length=10)
    machine_name = models.CharField(max_length=50)
    dept = models.CharField(max_length=50)
    venue = models.CharField(max_length=50)
    student_name = models.CharField(max_length=50)
    matric_number = models.CharField(max_length=10)
    machine = models.Manager()


class TimeTable(models.Model):
    machine_id = models.ForeignKey(Machine, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    course = models.CharField(max_length=50)
    venue = models.CharField(max_length=50)
    course_code = models.CharField(max_length=10)
    course_lecturer = models.CharField(max_length=50)
    timetable = models.Manager()


class AttendanceReport(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    dept = models.CharField(max_length=50)
    course_code = models.CharField(max_length=10)
    course_lecturer = models.CharField(max_length=50)
    matric_number = models.CharField(max_length=10)
    status = models.CharField(max_length=10)
    attendance_score = models.IntegerField()
    attendance_report = models.Manager()


class AdminManager(BaseUserManager):
    def create_user(self, admin_email, password=None, **extra_fields):
        if not admin_email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(admin_email)
        user = self.model(admin_email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, admin_email, admin_password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(admin_email, admin_password, **extra_fields)


class Admin(AbstractBaseUser):
    admin_fname = models.CharField(max_length=30)
    admin_lname = models.CharField(max_length=30)
    admin_email = models.EmailField(max_length=255, unique=True)
    admin_dept = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    admin_password = models.CharField(max_length=128)  # Default value

    is_superuser = models.BooleanField(default=True)

    objects = AdminManager()

    USERNAME_FIELD = 'admin_email'
    REQUIRED_FIELDS = ['admin_fname', 'admin_lname', 'admin_dept']

    class Meta:
        app_label = 'attendance_proj'

    def __str__(self):
        return self.admin_email


class Student_comp_sci_100L(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=100)
    matric_num = models.CharField(max_length=20, unique=True)
    CSC_101 = models.IntegerField(default=0)
    CSC_102 = models.IntegerField(default=0)
    CSC_105 = models.IntegerField(default=0)
    CSC_111 = models.IntegerField(default=0)
    level = models.IntegerField(default=100)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)

    def __str__(self):
        return self.student_name


# STAFF MODEL
class Staff(models.Model):
    staff_id = models.CharField(max_length=20, unique=True)
    staff_name = models.CharField(max_length=50)
    staff_dept = models.CharField(max_length=50)
    total_attendance_score = models.IntegerField()
    remarks = models.CharField(max_length=100)


# STAFF EVENTS 1 CONFERENCE MODEL, 2 WORKSHOP MODEL, 3 SEMINAR MODEL, 4 TRAINING MODEL, 5 RETREAT MODEL, 6 MEETING MODEL
from django.db import models
from django.utils import timezone
from datetime import date

today = date.today()
today.strftime("%d/%m/%Y")
today_format = today.strftime("%d/%m/%Y")




from django.db import models
from django.utils import timezone
from datetime import datetime




def get_current_time():
    return timezone.now().time()


class staff_Conference(models.Model):
    machine_id = models.CharField(max_length=50, blank=True, null=True)

    # ✅ NEW FIELD (ADDED ONLY)
    staff_rfid = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Staff RFID card number"
    )

    staff_id = models.CharField(max_length=20, unique=True)
    staff_name = models.CharField(max_length=200)
    staff_gender = models.CharField(max_length=20, blank=True, null=True)
    staff_dept = models.CharField(max_length=100)
    staff_faculty = models.CharField(max_length=100, blank=True, null=True)
    staff_title = models.CharField(max_length=100, blank=True, null=True)
    staff_category = models.CharField(max_length=100, blank=True, null=True)

    conference_title = models.CharField(max_length=500, default="conference")
    conference_venue = models.CharField(max_length=500, default="venue")
    conference_date = models.DateField(default=timezone.now)
    conference_time = models.TimeField(default=get_current_time)

    conference_type = models.CharField(max_length=100, default="type conf")
    conference_category = models.CharField(max_length=200, default="category")

    remarks = models.CharField(max_length=100, default="Not Marked")
    attendance_score = models.IntegerField(default=0)

    objects = models.Manager()  # default manager


class Workshop(models.Model):
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    workshop_name = models.CharField(max_length=50)
    workshop_venue = models.CharField(max_length=50)
    workshop_date = models.DateField()
    workshop_time = models.TimeField()
    clock_in = models.TimeField()
    clock_out = models.TimeField()
    workshop = models.Manager()


class Seminar(models.Model):
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    seminar_name = models.CharField(max_length=50)
    seminar_venue = models.CharField(max_length=50)
    seminar_date = models.DateField()
    seminar_time = models.TimeField()
    clock_in = models.TimeField()
    clock_out = models.TimeField()
    seminar = models.Manager()


class Training(models.Model):
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    training_name = models.CharField(max_length=50)
    training_venue = models.CharField(max_length=50)
    training_date = models.DateField()
    training_time = models.TimeField()
    clock_in = models.TimeField()
    clock_out = models.TimeField()
    training = models.Manager()


class Mass(models.Model):
    staff_id = models.ForeignKey(Staff, on_delete=models.CASCADE)
    retreat_name = models.CharField(max_length=50)
    retreat_venue = models.CharField(max_length=50)
    retreat_date = models.DateField()
    retreat_time = models.TimeField()
    clock_in = models.TimeField()
    clock_out = models.TimeField()
    retreat = models.Manager()

    staff = models.Manager()


#  COMPUTER SCIENCE MODEL 100 - 400L

class Comp_sci_100l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    CSC_101 = models.IntegerField(default=0)
    CSC_102 = models.IntegerField(default=0)
    CSC_105 = models.IntegerField(default=0)
    CSC_111 = models.IntegerField(default=0)
    level = models.IntegerField(default=100)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Comp_sci_200l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    CSC_201 = models.IntegerField(default=0)
    CSC_202 = models.IntegerField(default=0)
    CSC_203 = models.IntegerField(default=0)
    CSC_204 = models.IntegerField(default=0)
    level = models.IntegerField(default=200)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Comp_sci_300l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    CSC_301 = models.IntegerField(default=0)
    CSC_302 = models.IntegerField(default=0)
    CSC_303 = models.IntegerField(default=0)
    CSC_304 = models.IntegerField(default=0)
    level = models.IntegerField(default=300)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Comp_sci_400l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    CSC_401 = models.IntegerField(default=0)
    CSC_402 = models.IntegerField(default=0)
    CSC_403 = models.IntegerField(default=0)
    CSC_404 = models.IntegerField(default=0)
    level = models.IntegerField(default=400)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


# political SCIENCE MODEL 100 - 400L
class Pol_sci_100l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    POL_101 = models.IntegerField(default=0)
    POL_102 = models.IntegerField(default=0)
    POL_103 = models.IntegerField(default=0)
    POL_104 = models.IntegerField(default=0)
    level = models.IntegerField(default=100)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Pol_sci_200l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    POL_201 = models.IntegerField(default=0)
    POL_202 = models.IntegerField(default=0)
    POL_203 = models.IntegerField(default=0)
    POL_204 = models.IntegerField(default=0)
    level = models.IntegerField(default=200)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Pol_sci_300l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    POL_301 = models.IntegerField(default=0)
    POL_302 = models.IntegerField(default=0)
    POL_303 = models.IntegerField(default=0)
    POL_304 = models.IntegerField(default=0)
    level = models.IntegerField(default=300)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Pol_sci_400l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    POL_401 = models.IntegerField(default=0)
    POL_402 = models.IntegerField(default=0)
    POL_403 = models.IntegerField(default=0)
    POL_404 = models.IntegerField(default=0)
    level = models.IntegerField(default=400)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


#  ECONOMICS MODEL 100 - 400L
class Econ_100l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    ECO_101 = models.IntegerField(default=0)
    ECO_102 = models.IntegerField(default=0)
    ECO_103 = models.IntegerField(default=0)
    ECO_104 = models.IntegerField(default=0)
    level = models.IntegerField(default=100)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Econ_200l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    ECO_201 = models.IntegerField(default=0)
    ECO_202 = models.IntegerField(default=0)
    ECO_203 = models.IntegerField(default=0)
    ECO_204 = models.IntegerField(default=0)
    level = models.IntegerField(default=200)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Econ_300l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    ECO_301 = models.IntegerField(default=0)
    ECO_302 = models.IntegerField(default=0)
    ECO_303 = models.IntegerField(default=0)
    ECO_304 = models.IntegerField(default=0)
    level = models.IntegerField(default=300)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)


class Econ_400l(models.Model):
    matric_num = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    ECO_401 = models.IntegerField(default=0)
    ECO_402 = models.IntegerField(default=0)
    ECO_403 = models.IntegerField(default=0)
    ECO_404 = models.IntegerField(default=0)
    level = models.IntegerField(default=400)
    week = models.IntegerField(default=1)
    total_attendance_score = models.IntegerField(default=0)

    # LAW 100-400L MODELS
    class Law_100l(models.Model):
        matric_num = models.CharField(max_length=20, unique=True)
        student_name = models.CharField(max_length=50)
        LAW_101 = models.IntegerField(default=0)
        LAW_102 = models.IntegerField(default=0)
        LAW_103 = models.IntegerField(default=0)
        LAW_104 = models.IntegerField(default=0)
        level = models.IntegerField(default=100)
        week = models.IntegerField(default=1)
        total_attendance_score = models.IntegerField(default=0)

    class Law_200l(models.Model):
        mateic_num = models.CharField(max_length=20, unique=True)
        student_name = models.CharField(max_length=50)
        LAW_201 = models.IntegerField(default=0)
        LAW_202 = models.IntegerField(default=0)
        LAW_203 = models.IntegerField(default=0)
        LAW_204 = models.IntegerField(default=0)
        level = models.IntegerField(default=200)
        week = models.IntegerField(default=1)
        total_attendance_score = models.IntegerField(default=0)

    class Law_300l(models.Model):
        matric_num = models.CharField(max_length=20, unique=True)
        student_name = models.CharField(max_length=50)
        LAW_301 = models.IntegerField(default=0)
        LAW_302 = models.IntegerField(default=0)
        LAW_303 = models.IntegerField(default=0)
        LAW_304 = models.IntegerField(default=0)
        level = models.IntegerField(default=300)
        week = models.IntegerField(default=1)
        total_attendance_score = models.IntegerField(default=0)

    class Law_400l(models.Model):
        matric_num = models.CharField(max_length=20, unique=True)
        student_name = models.CharField(max_length=50)
        LAW_401 = models.IntegerField(default=0)
        LAW_402 = models.IntegerField(default=0)
        LAW_403 = models.IntegerField(default=0)
        LAW_404 = models.IntegerField(default=0)

    @classmethod
    def import_comp_sci_100l_csv(cls, csv_directory_path):
        csv_files = [file for file in os.listdir(csv_directory_path) if file.endswith('.csv')]
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(csv_directory_path, x)), reverse=True)
        latest_csv_file = csv_files[0]
        latest_csv_file_path = os.path.join(csv_directory_path, latest_csv_file)

        with open(latest_csv_file_path, mode='r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row if present
            for row in reader:
                matric_num_value = row[3]
                student_name_value = row[4]
                student, created = Comp_sci_100l.objects.get_or_create(
                    matric_num=matric_num_value,
                    defaults={'student_name': student_name_value}
                )
                attendance = cls(
                    matric_num=student,
                    student_name=student_name_value,
                )
                attendance.save()

# student event model
class Student_event(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=50)
    event_name = models.CharField(max_length=50)
    event_date = models.DateField()
    event_time = models.TimeField()
    event = models.Manager()

# 100L STUDENTS
class VUA_100l_mass_students(models.Model):
    student_matric_no = models.CharField(max_length=20, unique=True)
    student_fname = models.CharField(max_length=50)
    student_lname = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=20,default="not specified")
    student_level = models.IntegerField(default=100)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)
    student_total_attendance_score = models.IntegerField(default=0)
    student_remarks = models.CharField(max_length=100)
    student_event = models.Manager()


# 200l students
class VUA_200l_mass_students(models.Model):
    student_matric_no = models.CharField(max_length=20, unique=True)
    student_fname = models.CharField(max_length=50)
    student_lname = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=20,default="not specified")
    student_level = models.IntegerField(default=200)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)
    student_total_attendance_score = models.IntegerField(default=0)
    student_remarks = models.CharField(max_length=100)
    student_event = models.Manager()

# 300l STUDENTS
class VUA_300l_mass_students(models.Model):
    student_matric_no = models.CharField(max_length=20, unique=True)
    student_fname = models.CharField(max_length=50)
    student_lname = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=20,default="not specified")
    student_level = models.IntegerField(default=300)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)
    student_total_attendance_score = models.IntegerField(default=0)
    student_remarks = models.CharField(max_length=100)
    student_event = models.Manager()

# 400L STUDENTS
class VUA_400l_mass_students(models.Model):
    student_matric_no = models.CharField(max_length=20, unique=True)
    student_fname = models.CharField(max_length=50)
    student_lname = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=20,default="not specified")
    student_level = models.IntegerField(default=400)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)
    student_total_attendance_score = models.IntegerField(default=0)
    student_remarks = models.CharField(max_length=100)
    student_event = models.Manager()


# 500L  STUDENTS
class VUA_500l_mass_students(models.Model):
    student_matric_no = models.CharField(max_length=20, unique=True)
    student_fname = models.CharField(max_length=50)
    student_lname = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=20,default="not specified")
    student_level = models.IntegerField(default=500)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)
    student_total_attendance_score = models.IntegerField(default=0)
    student_remarks = models.CharField(max_length=100)
    student_event = models.Manager()

from django.db import models
from django.utils.timezone import now  # Use this for generating current timestamp


class Staff_mass_records(models.Model):
    staff_id = models.CharField(max_length=20, unique=True)
    staff_rfid = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Staff RFID card number"
    )
    staff_fname = models.CharField(max_length=50)
    staff_lname = models.CharField(max_length=50)
    staff_gender = models.CharField(max_length=20, default="not specified")
    staff_title = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    faculty = models.CharField(max_length=50)
    staff_category = models.CharField(max_length=50)

    # Weekly clock-in times (allow null values for unused or missing times)
    week_1 = models.IntegerField(default=0)
    week_2 = models.IntegerField(default=0)
    week_3 = models.IntegerField(default=0)
    week_4 = models.IntegerField(default=0)
    week_5 = models.IntegerField(default=0)
    week_6 = models.IntegerField(default=0)
    week_7 = models.IntegerField(default=0)
    week_8 = models.IntegerField(default=0)
    week_9 = models.IntegerField(default=0)
    week_10 = models.IntegerField(default=0)
    week_11 = models.IntegerField(default=0)
    week_12 = models.IntegerField(default=0)

    staff_total_attendance_score = models.IntegerField(default=0)
    staff_remarks = models.CharField(max_length=100, blank=True, null=True)

    staff_event = models.Manager()

    def __str__(self):
        return f"{self.staff_fname} {self.staff_lname} ({self.staff_id})"





