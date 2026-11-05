# crimes/urls.py
from django.urls import path
from . import views

app_name = 'crimes'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('officer/', views.officer_dashboard, name='officer_dashboard'),
    path('investigator/', views.investigator_dashboard, name='investigator_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # FIR Management
    path('fir/create/', views.FIRCreateView.as_view(), name='fir_create'),
    path('fir/<int:pk>/', views.fir_detail, name='fir_detail'),
    path('fir/<int:pk>/biometric/', views.fir_biometric, name='fir_biometric'),
    path('fir/list/', views.FIRListView.as_view(), name='fir_list'),
    path('fir/<int:pk>/update-status/', views.fir_update_status, name='fir_update_status'),
    path('fir/<int:pk>/assign-investigator/', views.assign_investigator, name='assign_investigator'),
    
    # Witness Management
    path('fir/<int:fir_id>/witness/add/', views.add_witness, name='add_witness'),
    path('fir/<int:fir_id>/', views.view_fir, name='view_fir'),
    
    # Evidence Management
    path('fir/<int:fir_id>/evidence/add/', views.add_evidence, name='add_evidence'),
    path('evidence/<int:evidence_id>/custody/', views.update_evidence_custody, name='update_evidence_custody'),
    
    # Investigation Updates
    path('fir/<int:fir_id>/investigation/add/', views.add_investigation_update, name='add_investigation_update'),
    path('fir/<int:pk>/print/', views.print_fir, name='print_fir'),

    # Criminal Database
    path('criminal/', views.CriminalRecordListView.as_view(), name='criminal_list'),
    path('criminal/add/', views.add_criminal_record, name='add_criminal_record'),
    path('criminal/<int:pk>/', views.criminal_detail, name='criminal_detail'),
    path('criminal/search/', views.search_criminal, name='search_criminal'),
    path('analytics/', views.crime_analytics, name='crime_analytics'),
    

    # Add this to your urls.py
    path('criminal/<int:pk>/edit/', views.edit_criminal_record, name='edit_criminal'),
    
    # Reports
    path('reports/', views.generate_report, name='generate_report'),
    path('reports/', views.generate_report, name='reports'),
    path('help/', views.help_support, name='help_support'),
    path('user-manual/', views.user_manual, name='user_manual'),



    
    # API Endpoints
    path('api/verify-mobile/', views.verify_mobile_otp, name='verify_mobile_otp'),
    path('api/verify-aadhaar/', views.verify_aadhaar, name='verify_aadhaar'),
    path('api/check-biometric/', views.check_biometric_match, name='check_biometric_match'),
    path('api/station/<int:station_id>/', views.get_police_station_details, name='get_station_details'),
    
    # Public Endpoints
    path('verify/<uuid:uuid>/', views.verify_fir_public, name='verify_fir_public'),
    
    # Utility
path('fir/search/', views.fir_search_view, name='search_fir'),
    path('criminal/create/', views.CriminalCreateView.as_view(), name='criminal_create'),
    path('criminal/<int:pk>/update/', views.CriminalUpdateView.as_view(), name='criminal_update'),
    path('criminal/<int:pk>/delete/', views.CriminalDeleteView.as_view(), name='criminal_delete'),



    path('fir/<int:pk>/edit/', views.edit_fir, name='fir_edit'),
    path('fir/<int:pk>/share/', views.share_fir, name='fir_share'),
    path('fir/<int:pk>/delete/', views.delete_fir, name='fir_delete'),
    path('fir/<int:pk>/generate-qr/', views.generate_fir_qr, name='fir_generate_qr'),

    path("criminal/export/csv/", views.export_criminals_csv, name="export_criminals_csv"),
    path("criminal/export/excel/", views.export_criminals_excel, name="export_criminals_excel"),
    path("criminal/export/pdf/", views.export_criminals_pdf, name="export_criminals_pdf"),



    # forensic routes
    path("forensic/upload/", views.forensic_upload_reports, name="forensic_upload"),
    path("forensic/biometric/", views.forensic_biometric_matching, name="forensic_biometric"),
    path("forensic/evidence/", views.forensic_evidence_verification, name="forensic_evidence"),




     # Authority / Admin actions
    path("authority/evidence/", views.review_evidence_chain, name="review_evidence_chain"),
    path("authority/ai-matches/", views.view_ai_match_explanations, name="ai_match_explanations"),
    path("authority/warrants/", views.authorize_warrants, name="authorize_warrants"),
    path("authority/rejections/", views.review_complaint_rejections, name="review_complaint_rejections"),
]