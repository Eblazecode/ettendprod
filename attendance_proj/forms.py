from django import forms
from .models import Student, Attendance, Machine, TimeTable, Admin, AttendanceReport


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'  # ['student_id', 'student_name', 'student_email', 'student_dept', 'student_course', 'student_address', 'student_dob']


# processing  admin registration form
class AdminForm(forms.ModelForm):
    class Meta:
        model = Admin
        fields = ['admin_fname', 'admin_lname',
                  'admin_email',
                  'admin_password',
                  'admin_dept']
        widgets = {
            'admin_password': forms.PasswordInput()
        }

        # processing login fo


class AdminLoginForm(forms.Form):
    admin_email = forms.EmailField(label="Admin Email", max_length=50)
    admin_password = forms.CharField(label="Admin Password", max_length=50, widget=forms.PasswordInput)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['admin_password'])
        if commit:
            user.save()
        return user


class Upload_timetable_form(forms.Form):
    file = forms.FileField()


class Upload_registered_students(forms.Form):
    file = forms.FileField()
class Upload_students_database(forms.Form):
    file = forms.FileField()

class Upload_staff_records(forms.Form):
    file = forms.FileField()

class Upload_staff_events_attendance(forms.Form):
    file = forms.FileField()

class Upload_students_events_attendance(forms.Form):
    file = forms.FileField()

class MachineForm(forms.Form):
    file = forms.FileField()


# countries/forms.py


class UniversityDepartmentForm(forms.Form):
    DEPARTMENT_CHOICES = [
        ('', 'Select a department'),
        ('Engineering', 'Engineering'),
        ('Science', 'Science'),
        ('Arts', 'Arts'),
    ]

    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)


class CourseForm(forms.Form):
    course = forms.ChoiceField(choices=[])

