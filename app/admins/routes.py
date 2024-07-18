from typing import List, Tuple
import pytz
from datetime import datetime, timedelta
from flask import Blueprint, Response, current_app, render_template, redirect, request, flash, session, url_for
from flask_login import logout_user
import folium
from sqlalchemy import and_, desc, extract, func, or_
from app.admins.models import Admin 
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, send_assignment_email, send_status_update_email
from app.officers.models import CaseReport, Officers
from app.posts.models import Crime, Message
from app.users.models import User
from functools import wraps
from folium.plugins import HeatMap
from sqlalchemy.exc import SQLAlchemyError


admins = Blueprint('admins', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            flash('You need to be logged in as an admin to access the page.', 'danger')
            return redirect(url_for('admins.adminIndex'))
        return f(*args, **kwargs)
    return decorated_function

# getting coordinates
def get_coordinates() -> List[Tuple[float, float]]:
    try:
        coordinates = db.session.query(Crime.latitude, Crime.longitude).filter(
            and_(Crime.latitude.isnot(None), Crime.longitude.isnot(None))
        ).all()
        
        valid_coordinates = [
            (float(lat), float(lon)) 
            for lat, lon in coordinates 
            if lat is not None and lon is not None and lat != '' and lon != ''
        ]
        
        return valid_coordinates
    except Exception as e:
        current_app.logger.error(f"Error in get_coordinates: {str(e)}")
        return []

# function to get crime by month
def get_crime_data_by_month():
    crime_data = {f'{i:02d}': 0 for i in range(1, 13)}
    results = db.session.query(
        db.extract('month', Crime.date_crime_received).label('month'),
        db.func.count(Crime.crime_id).label('count')
    ).group_by('month').all()

    for month, count in results:
        crime_data[f'{month:02d}'] = count

    return crime_data

# getting daily distribution
def get_daily_crime_data():
    timezone = pytz.timezone('Africa/Nairobi')
    now = datetime.now(timezone)

    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    end_of_week = start_of_week + timedelta(days=6)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

    crime_dist = {day: {'crimes': 0} for day in range(7)}

    crime_results = db.session.query(
        Crime.date_crime_received,
        func.count(Crime.crime_id).label('count')
    ).filter(
        Crime.date_crime_received >= start_of_week,
        Crime.date_crime_received <= end_of_week
    ).group_by(Crime.date_crime_received).all()

    for date_crime_received, count in crime_results:
        
        date_crime_received = date_crime_received.astimezone(timezone)
        day_of_week = date_crime_received.weekday()  
        crime_dist[day_of_week]['crimes'] = count

    return crime_dist

# getting monthly averages
def get_monthly_averages():
    crime_average = {f'{i:02d}': 0 for i in range(1, 13)}

    crime_results = db.session.query(
        extract('month', Crime.date_crime_received).label('month'),
        func.count(Crime.crime_id).label('count')
    ).group_by('month').all()

    for month, count in crime_results:
        crime_average[f'{month:02d}'] = count

    return crime_average

#getting annual crime distribution
def get_annual_crime_data():
    annual_crime_data = db.session.query(
        func.strftime('%Y', Crime.date_crime_received).label('year'),
        func.count(Crime.crime_id).label('crime_count')
    ).group_by(func.strftime('%Y', Crime.date_crime_received)).all()

    return annual_crime_data

# admin login page route
@admins.route('/admin/', methods=['GET', 'POST'])
def adminIndex():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' and password == '':
            flash('Please fill all the field', category='danger')
            return redirect('/admin/')
        else:
            admins = Admin().query.filter_by(username=username).first()
            if admins and check_password_hash(admins.password,password):
                session['admin_id']=admins.id
                session['admin_name']=admins.username
                flash('Login Successfully', category='success')
                return redirect('/admin/dashboard')
            else:
                flash("Invalid Email and Password", category='danger')
                return redirect('/admin/')
    else:   
        return render_template('admin/index.html', 
        title='Admin Login')

@admins.route('/admin/dashboard')
@admin_required
def adminDashboard():
    annual_crime_data = get_annual_crime_data()
    crime_average = get_monthly_averages()
    crime_data = get_crime_data_by_month()
    crime_dist = get_daily_crime_data()
    user_count = User.query.count()
    officer_count = Officers.query.count()
    crime_count = Crime.query.count()
    
    
    total_user = user_count + officer_count
    
    recovered_count = Crime.query.filter_by(crime_status='Recovered').count()
    crimes = Crime.query.all()
    crime_locations = [crime.to_dict() for crime in crimes]

    return render_template('admin/dashboard.html', user_count=total_user,
                           crime_count=crime_count, 
                           recovered_count=recovered_count, 
                           crime_data=crime_data,
                           crime_average=crime_average,
                           annual_crime_data=annual_crime_data,
                           crime_locations=crime_locations,
                           crime_dist=crime_dist)

# change admin password
@admins.route('/admin/change-admin-password',methods=["POST","GET"])
@admin_required
def adminChangePassword():
    admin = Admin.query.get(1)  
    
    if request.method == 'POST':
        if 'update_profile' in request.form:
            username = request.form.get('username')
            email = request.form.get('email')
            
            if not username or not email:
                flash('Please fill all fields', 'danger')
            else:
                admin.username = username
                admin.admin_email = email  
                db.session.commit()
                flash('Profile updated successfully', 'success')
            
        elif 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                flash('Please fill all password fields', 'danger')
            elif not check_password_hash(admin.password, current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            else:
                admin.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Password changed successfully', 'success')
        
        return redirect(url_for('admins.adminChangePassword'))
    return render_template('admin/admin-change-password.html',title='Admin Settings',admin=admin)


@admins.route('/admin/reports')
@admin_required
def reports():
    search_query = request.args.get('search_query', '')
    try:
        if search_query:
            crimes = Crime.query.filter(
                Crime.incident_location.ilike(f'%{search_query}%') |
                Crime.issued_by.ilike(f'%{search_query}%') |
                Crime.date_of_incident.ilike(f'%{search_query}%') |
                Crime.time_of_incident.ilike(f'%{search_query}%') |
                Crime.date_crime_received.ilike(f'%{search_query}%') |
                Crime.crime_status.ilike(f'%{search_query}%') |
                Crime.incident_nature.ilike(f'%{search_query}%')
            ).order_by(desc(Crime.date_crime_received)).all()
        else:
            crimes = Crime.query.order_by(desc(Crime.date_crime_received)).all()
    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        flash("An error occurred while fetching reports.", "danger")
        return redirect(url_for('admins.reports'))
    
    if not crimes:
        flash("No reports found.", "info")
    
    return render_template('admin/reports.html', title='Reports Dashboard', crimes=crimes)

@admins.route('/admin/crime_status/<int:crime_id>', methods=['POST'])
@admin_required
def updateCrimeStatus(crime_id):
    try:
        crime = Crime.query.get_or_404(crime_id)
        crime_status = request.form.get('crime_status')
        if crime_status:
            crime.crime_status = crime_status
            db.session.commit()
            
            # Send email to the user who posted the report
            send_status_update_email(crime)
            
            flash(f'Crime status updated to {crime_status}.', 'success')
        else:
            flash('Failed to update crime status.', 'danger')
    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        db.session.rollback()
        flash("An error occurred. Please try again later.", "danger")
    
    return redirect(url_for('admins.crimeStatus'))

@admins.route('/admin/crime_status')
@admin_required
def crimeStatus():
    search_crime = request.args.get('search_crime', '')
    try:
        if search_crime:
            crimes_status = Crime.query.filter(
                Crime.incident_location.ilike(f'%{search_crime}%') |
                Crime.issued_by.ilike(f'%{search_crime}%') |
                Crime.date_of_incident.ilike(f'%{search_crime}%') |
                Crime.time_of_incident.ilike(f'%{search_crime}%') |
                Crime.date_crime_received.ilike(f'%{search_crime}%') |
                Crime.crime_status.ilike(f'%{search_crime}%')
            ).order_by(desc(Crime.date_crime_received)).all()
        else:
            crimes_status = Crime.query.order_by(desc(Crime.date_crime_received)).all()
    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        flash("An error occurred while fetching crime status reports.", "danger")
        return redirect(url_for('admins.crimeStatus'))
    
    if not crimes_status:
        flash("No crime status reports found.", "info")
    
    return render_template('admin/crime_status.html', title='Crime Status', crimes_status=crimes_status)

@admins.route('/admin/crime_details/<int:crime_id>', methods=['POST', 'GET'])
@admin_required
def crimeDetails(crime_id):
    try:
        crime_details = Crime.query.filter_by(crime_id=crime_id).all()
        if crime_details is None:
            flash("Crime details not found.", "warning")
            return redirect(url_for('admins.reports'))
    except:
        current_app.logger.error("Database error:")
        
        flash("An error occurred while fetching the reports crime details. Please try again later.", "danger")
        
        return redirect(url_for('admins.reports'))
    
    return render_template('admin/crime_details.html', crime_details=crime_details)

@admins.route('/admin/download-image/<int:crime_id>')
@admin_required
def download_image(crime_id):
    crime_details = Crime.query.get_or_404(crime_id)
    if not crime_details.crime_file_upload:
        flash('No image found', 'danger')
        return redirect(url_for('admins.crimeDetails', crime_id=crime_id))
    
    return Response(
        crime_details.crime_file_upload,
        mimetype=crime_details.crime_mimetype,
        headers={
            "Content-Disposition": f"attachment;filename={crime_details.crime_file_name}"
        }
    )

@admins.route('/admin/crimes_details/<int:crime_id>', methods=['POST', 'GET'])
@admin_required
def caseReport(crime_id):
    if request.method == 'POST':
        crime_type = request.form.get('crime_type')
        location = request.form.get('location')
        phone_number = request.form.get('phone_number')
        date = request.form.get('date')
        time = request.form.get('time')
        description = request.form.get('description')
        evidence = request.form.get('evidence')
        urgency = request.form.get('urgency')
        deadline = request.form.get('deadline')

        case_report = CaseReport(crime_type=crime_type,
                                 location=location,
                                 date=date,
                                 time=time,
                                 description=description,
                                 evidence=evidence,
                                 urgency=urgency,
                                 phone_number=phone_number,
                                 deadline=deadline)
        try:
            db.session.add(case_report)
            db.session.commit()
            flash('Success. Case Report created', 'success')
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            flash("An error occurred when creating report. Please try again later.", "danger")
        
        return redirect(url_for('admins.crimeDetails', crime_id=crime_id))

    return redirect(url_for('admins.crimeDetails', crime_id=crime_id))


@admins.route('/admin/case-reports')
@admin_required
def case_reports():
    search_case_reports = request.args.get('search_case_reports', '')
    try:
        if search_case_reports:
            cases = CaseReport.query.filter(
                CaseReport.location.ilike(f'%{search_case_reports}%') |
                CaseReport.status.ilike(f'%{search_case_reports}%') |
                CaseReport.date.ilike(f'%{search_case_reports}%') |
                CaseReport.time.ilike(f'%{search_case_reports}%') |
                CaseReport.crime_type.ilike(f'%{search_case_reports}%') |
                CaseReport.created_at.ilike(f'%{search_case_reports}%') |
                CaseReport.urgency.ilike(f'%{search_case_reports}%')
            ).order_by(desc(CaseReport.created_at)).all()
        else:
            cases = CaseReport.query.order_by(desc(CaseReport.created_at)).all()
        
        officers = Officers.query.all()
    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        flash("An error occurred while retrieving the reports.", "error")
        return redirect(url_for('admins.case_reports'))
    
    if not cases:
        flash("No case reports found.", "info")
    
    return render_template('admin/case_reports.html', cases=cases, officers=officers)


@admins.route('/admin/case_report_details/<int:report_id>', methods=['GET', 'POST'])
@admin_required
def case_report_details(report_id):
    report = CaseReport.query.get_or_404(report_id)
    return render_template('admin/case_report_details.html', report=report)

@admins.route('/admin/edit_case_report/<int:report_id>', methods=['GET', 'POST'])
@admin_required
def edit_case_report(report_id):
    
    report = CaseReport.query.get_or_404(report_id)
    officers = Officers.query.all()

    if request.method == 'POST':
        report.crime_type = request.form['crime_type']
        report.location = request.form['location']
        report.date = request.form['date']
        report.time = request.form['time']
        report.description = request.form['description']
        report.evidence = request.form['evidence']
        report.urgency = request.form['urgency']
        report.deadline = request.form['deadline']
        
        assigned_officer_id = request.form.get('assigned_officer')
        if assigned_officer_id:
            new_officer_id = int(assigned_officer_id)
            if new_officer_id != report.assigned_officer_id:
                report.assigned_officer_id = new_officer_id
                assigned_officer = Officers.query.get(new_officer_id)
                if assigned_officer:
                    send_assignment_email(assigned_officer, report)
        else:
            report.assigned_officer_id = None

        try:
            db.session.commit()
            flash('Report updated successfully', 'success')
            return redirect(url_for('admins.case_report_details', report_id=report.report_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('admin/edit_case_report.html', report=report, officers=officers)

    

@admins.route('/admin/analytics')
@admin_required
def analytics():
    try:
        coordinates = get_coordinates()
        
        if not coordinates:
            flash("No valid coordinates found.", "warning")
            return redirect(url_for('admins.analytics'))
        
        map_center = [
            sum(lat for lat, _ in coordinates) / len(coordinates),
            sum(lon for _, lon in coordinates) / len(coordinates)
        ]
        
        m = folium.Map(location=map_center, zoom_start=6)
        
        HeatMap(coordinates).add_to(m)
        
        map_html = m._repr_html_()
        
        crime_data = db.session.query(
            Crime.incident_location,
            db.func.count(Crime.crime_id)
        ).group_by(Crime.incident_location).all()
        
        crime_labels = [row[0] for row in crime_data if row[0] is not None]
        crime_counts = [row[1] for row in crime_data if row[0] is not None]
        
        return render_template('admin/analytics.html',
                               title='Analytics Dashboard',
                               crime_labels=crime_labels,
                               crime_counts=crime_counts,
                               map_html=map_html)
    
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in analytics: {str(e)}")
        flash("An error occurred while querying the database.", "danger")
    except Exception as e:
        current_app.logger.error(f"Unexpected error in analytics: {str(e)}")
        flash("An unexpected error occurred generating the analysis.", "danger")
    
    return redirect(url_for('admins.analytics'))

@admins.route('/admin/notifications')
@admin_required
def notifications():
    search_notifications = request.args.get('search_notifications', '')
    messages = []  

    try:
        if search_notifications:
            messages = Message.query.filter(
                or_(
                    Message.incident_location.ilike(f'%{search_notifications}%'),
                    Message.issued_by.ilike(f'%{search_notifications}%'),
                    Message.date_of_incident.ilike(f'%{search_notifications}%'),
                    Message.time_of_incident.ilike(f'%{search_notifications}%'),
                    Message.date_received.ilike(f'%{search_notifications}%'),
                    Message.crime_status.ilike(f'%{search_notifications}%')
                )
            ).order_by(Message.date_received.desc()).all()
        else:
            messages = Message.query.order_by(Message.date_received.desc()).all()

        if not messages:
            flash("No messages found.", "info")

    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        flash("An error occurred while retrieving messages. Please try again later.", "danger")

    return render_template('/admin/notifications.html', messages=messages)

@admins.route('/admin/message/<int:id>', methods=['GET', 'POST'])
@admin_required
def view_message(id):
    try:
        message = Message.query.get(id)
        if message is None:
            flash("Message not found.", "warning")
            return redirect(url_for('admins.notifications'))

        if request.method == 'POST':
            message_reply = request.form.get('reply')
            if message_reply:
                message.reply = message_reply
                db.session.commit()
                
                flash('Success, Reply sent', 'success')
            else:
                flash('Failed to send reply.', 'danger')
            
            return redirect(url_for('admins.view_message', id=id))

    except Exception as e:
        current_app.logger.error(f"Database error: {e}")
        flash("An error occurred. Please try again later.", "danger")
        return redirect(url_for('admins.notifications'))

    return render_template('/admin/message_details.html', message=message)

@admins.route('/admin/logout')
@admin_required
def adminLogout():    
    if not session.get('admin_id'):
        return redirect('/admin/')
    if session.get('admin_id'):
        session['admin_id']=None
        session['admin_name']=None
        flash('You have been logged out.', category='info')
        logout_user()
    return redirect(url_for('admins.adminIndex'))
