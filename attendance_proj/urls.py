
from django.urls import path
from . import views
import os
from django.conf import settings    
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('student', views.student, name='student'),
    path('admin', views.admin, name='admin'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('success/', views.success_url, name='success_url'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('time_table/', views.upload_DAP_timetable, name='time_table'),
    path('admin_register/', views.admin_register, name='admin_register'),  # Example of adding a new URL pattern
    path('view_timetable/', views.view_timetable, name='view_timetable'),
    path('upload_machine_attendance/',views.machine_attendance_upload, name='machine_attendance'),    
    path('view_machine_attendance/',views.machine_upload_view, name='upload_view'),
    path('student_attendance/',views.generate_attendance, name='student_attendance'),
    path('get-courses/<str:department>/', views.get_courses, name='get_courses'),
    path('process-selection/', views.process_selection, name='process_selection'),
    path('unschduled_attendance/', views.unscheduled_events_attendance, name='unscheduled_attendance'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('summary_attendance', views.summary_attendance, name='summary_attend'),
    path('track_attendance/', views.track_attendance, name='track_attendance'),
    path('upload_registered_students/', views.Update_weekely_attendance_DB, name='dept_upload'),
    path('upload_staff_biometrics_data',views.staff_biometrics_upload,name='staff_biometrics_upload'),
    path('staff_biometrics_view',views.staff_biometrics_upload_view,name='staff_biometrics_view'),
    path('staff_event_creation',views.staff_events_creation,name='staff_event_create'),
    path('score_card/', views.attendance_score_card, name='scorecard'),
    path('staff_event_attendance/', views.staff_event_attendance_generator, name='staff_event_attendance'),

    # student events
    path("upload_student_records_DB/",views.upload_students_records_db,name="upload_student_records_db"),
    path("view_100l_student_records_DB/",views.view_uploaded_student_100_records,name="view_100l_student_records_db"),
    path('view_200l_student_records_DB/',views.view_uploaded_student_200_records,name='view_200l_student_records_db'),
    path('view_300l_student_records_DB/',views.view_uploaded_student_300l_records,name='view_300l_student_records_db'),
    path('view_400l_student_records_DB/',views.view_uploaded_student_400l_records,name='view_400l_student_records_db'),
    path('create_mass_attendance/',views.student_mass_attendance,name='create_mass_attendance'),
    path('weekly_student_attendance_view/',views.student_mass_attendance_generator,name='student_mass_attendance_view'),
    path('view_100L_student_mass_attendance/',views.view_mass_attendance_records,name='view_student_mass_attendance_level_100'),
    path('view_200L_student_mass_attendance/',views.view_mass_attendance_records,name='view_student_mass_attendance_level_200'),
    path('view_300L_student_mass_attendance/',views.view_mass_attendance_records,name='view_student_mass_attendance_level_300'),
    path('view_400L_student_mass_attendance/',views.view_mass_attendance_records,name='view_student_mass_attendance_level_400'),
    path('fetch_student_mass_absenteeism/',views.student_mass_absenteeism_generator,name='fetch_student_mass_absenteeism'),
    path('view_student_mass_absenteeism/',views.view_student_absenteeism_records,name='view_student_mass_absenteeism'),


    # STAFF MASS ATTENDANCE
    path('upload_staff_records_DB/',views.upload_staff_records_db,name='upload_staff_records_db'),
    path('view_staff_mass_attendance/', views.view_uploaded_staff_records_mass, name='staff_mass_attendance_upload_view'),
    path('create_staff_mass_attendance/',views.staff_mass_attendance,name='create_staff_mass_attendance'),
    path('staff_attendance_generator/',views.staff_mass_weekly_attendance_generator,name='staff_mass_attendance_view'),
    path('view_staff_mass_attendance/',views.view_mass_attendance_records,name='view_staff_mass_attendance'),
    path('fetch_weekly_staff_mass_absentees/',views.staff_mass_absenteeism_generator,name='fetch_staff_mass_absentees'),
    path('view_staff_mass_absenteeism/',views.view_staff_absenteeism_records,name='view_staff_mass_absenteeism'),

    # strictly conference events

    path('upload_staff_conference', views.upload_staff_conference, name='upload_staff_conference'),
    path("view_upload_staff_conference/", views.view_staff_conference, name="view_upload_staff_conference"),
    path('staff_event_creation_new', views.staff_events_creation_NEW, name='staff_event_create_new'),
    path("students/add/", views.add_student, name="add_student"),
    path("students/delete/", views.delete_students, name="delete_students"),



]





# Compare this snippet from attendanceapp/attendance_proj/forms.py: 