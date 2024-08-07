from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import logout_user
from sqlalchemy import func, or_
from app import db, send_officer_reset_email, send_status_admin_email
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.officers.models import CaseReport, Officers
from bs4 import BeautifulSoup

officers = Blueprint('officers', __name__)

def officer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('officer_id'):
            flash('You need to be logged in as an officer to access the page.', 'danger')
            return redirect(url_for('officers.officerLogin'))
        return f(*args, **kwargs)
    return decorated_function

@officers.route('/officer/login', methods=['GET', 'POST'])
def officerLogin():
  if  session.get('officer_id'):
        return redirect('/officer/officer-dashboard')
  if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        officer = Officers.query.filter_by(username=username).first()
        
        if officer:
            if check_password_hash(officer.password, password):
                session['officer_id']=officer.officer_id
                session['officer_username']=officer.username
                flash(f'Logged in successfully! Hello {username}', category='success')
                return redirect(url_for('officers.officerDashboard'))
            else: 
                flash('Incorrect password, try again.', category='danger')
        else:
            flash('Username does not exist.', category='danger')
    
  return render_template('officer/login.html')

@officers.route("/officer/reset-password", methods=['GET', 'POST'])
def resetRequest():
    if request.method == 'POST':
        officer_email = request.form.get('officer_email')
        officer = Officers.query.filter_by(officer_email=officer_email).first()
        if officer:
            send_officer_reset_email(officer)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('officers.officerLogin'))
        else:
            flash('Email does not exist', 'danger')
    return render_template('officer/officer-reset-request.html', title='Request Password Reset')

@officers.route("/officer/reset-password/<token>", methods=['GET', 'POST'])
def resetToken(token):
    officer = Officers.verify_officer_reset_token(token)
    if officer is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('officers.resetRequest'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('officer/officer-reset-token.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('officer/officer-reset-token.html')
        
        hashed_password = generate_password_hash(password)
        officer.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! Please log in', 'success')
        return redirect(url_for('officers.officerLogin'))
    
    return render_template('officer/officer-reset-token.html', title='Reset Password')

@officers.route('/officer/register', methods=['GET', 'POST'])
def officerRegister():
  if  session.get('officer_id'):
        return redirect('/officer/officer-dashboard')
  if request.method == 'POST':
        username = request.form.get('username')
        phonenumber = request.form.get('phoneNumber')
        officer_email = request.form.get('officer_email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        badge = request.form.get('badge')
        rank = request.form.get('rank')
        station = request.form.get('station')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        officer = Officers.query.filter_by(username=username).first()
        email = Officers.query.filter_by(officer_email=officer_email).first()
        new_phonenumber = Officers.query.filter_by(phonenumber=phonenumber).first()

        if officer:
          flash('Username already exists.', category='warning')
        elif len(phonenumber) < 10 or len(phonenumber) > 10:
            flash('Invalid phone number', category='warning')
        elif new_phonenumber:
            flash('Phone number already exists', category='warning')
        elif email:
          flash('Email already exists.', category='warning')
        elif len(username) < 2:
            flash('Username must be more than 1 characters.', category='warning')
        elif len(officer_email) < 4:
            flash('Email must be more than 4 characters.', category='warning')
        elif password1 != password2:
            flash('Password don\'t match.', category='warning')
        elif len(password1) < 8:
            flash('Password must be at least 8 characters.', category='warning')
        else:
            # add officer to database
            new_officer = Officers(username=username, 
                                phonenumber=phonenumber,
                                officer_email=officer_email, 
                                first_name=first_name,
                                last_name=last_name,
                                badge=badge,
                                rank=rank,
                                station=station,
                                password=generate_password_hash(
                                password1, 
                                method='pbkdf2:sha256'))
            db.session.add(new_officer)
            db.session.commit()
            flash('Account created! Login to Access the Dashboard', category='success')
            return redirect(url_for('officers.officerLogin'))
  return render_template('officer/registration.html')

@officers.route('/officer/officer-dashboard', methods=['GET', 'POST'])
@officer_required
def officerDashboard():
    if 'officer_id' not in session:
        return redirect(url_for('login'))

    officer_id = session['officer_id']
    
    officer = Officers.query.get(officer_id)
    if not officer:
        return redirect(url_for('officers.officerLogin'))

    all_cases = CaseReport.query.filter_by(assigned_officer_id=officer_id).all()
    all_cases_count = len(all_cases)

    completed_cases = CaseReport.query.filter_by(assigned_officer_id=officer_id, status='Solved').all()
    completed_cases_count = len(completed_cases)

    high_urgency_count = CaseReport.query.filter_by(
    assigned_officer_id=officer_id, 
    urgency='high'
    ).count()

    critical_urgency_count = CaseReport.query.filter_by(
        assigned_officer_id=officer_id, 
        urgency='critical'
    ).count()

    urgent_cases_count = high_urgency_count + critical_urgency_count

    recent_cases_count = CaseReport.query.filter(
        CaseReport.assigned_officer_id == officer_id,
        CaseReport.assigned_at >= (datetime.now() - timedelta(hours=24))
        ).count()
    
    recent_activities = db.session.query(
        CaseReport.report_id,
        CaseReport.crime_type,
        CaseReport.created_at
    ).filter_by(
        assigned_officer_id=officer_id
    ).order_by(CaseReport.created_at.desc()).limit(5).all()

    upcoming_deadlines = CaseReport.query.filter_by(
        assigned_officer_id=officer_id
    ).order_by(CaseReport.deadline).limit(5).all()

    now = datetime.now()

    for case in upcoming_deadlines:
        if isinstance(case.deadline, str):
            case_deadline = datetime.strptime(case.deadline, '%Y-%m-%d')
        else:
            case_deadline = case.deadline

        remaining = case_deadline - now

        if remaining.total_seconds() <= 0:
            days_overdue = abs(remaining.days)
            case.remaining_time = f"Overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}"
        else:
            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            case.remaining_time = f"{days}d {hours}h {minutes}m"
        
    case_stats = db.session.query(
        CaseReport.status, 
        func.count(CaseReport.report_id)
    ).filter_by(
        assigned_officer_id=officer_id
    ).group_by(CaseReport.status).all()

    status_labels = [stat[0] for stat in case_stats]
    status_counts = [stat[1] for stat in case_stats]

    return render_template('officer/officer-dashboard.html', 
                           all_cases_count=all_cases_count, 
                           completed_cases_count=completed_cases_count,
                           urgent_cases_count=urgent_cases_count,
                           recent_cases_count=recent_cases_count,
                           recent_activities=recent_activities,
                           upcoming_deadlines=upcoming_deadlines,
                           status_labels=status_labels,
                           status_counts=status_counts)

@officers.route('/officer/assigned-cases')
@officer_required
def assignedCase():
    officer_id = session['officer_id']

    search_assigned = request.args.get('search_assigned', '')
    try:
        if search_assigned:
            all_cases_assigned = CaseReport.query.filter(
                CaseReport.assigned_officer_id == officer_id
            ).filter(
                or_(
                CaseReport.crime_type.ilike(f'%{search_assigned}%') | 
                CaseReport.location.ilike(f'%{search_assigned}%') |
                CaseReport.date.ilike(f'%{search_assigned}%') |
                CaseReport.time.ilike(f'%{search_assigned}%') |
                CaseReport.created_at.ilike(f'%{search_assigned}%') |
                CaseReport.status.ilike(f'%{search_assigned}%') |
                CaseReport.urgency.ilike(f'%{search_assigned}%')
                )
            ).all()
        else:
            all_cases_assigned = CaseReport.query.filter_by(assigned_officer_id=officer_id).all()
    except:
        current_app.logger.error("Database error:")
        
        flash("No report with the keyword.", "warning")
        
        return redirect(url_for('officers.assignedCase'))
        

    return render_template('officer/assigned-cases.html', all_cases_assigned=all_cases_assigned)

@officers.route('/officer/case-details/<int:report_id>', methods=['POST','GET'])
@officer_required
def caseDetails(report_id):
    try:
        report = CaseReport.query.get_or_404(report_id)

        if report is None:
                flash("Case details not found.", "warning")
                return redirect(url_for('officers.reports'))
        
        if request.method == 'POST':
            officer_report_text = request.form.get('officer_report')
            media = request.files['media']
            filename = secure_filename(media.filename)
            mimetype = media.mimetype
            
            report.reports = officer_report_text
            report.media = media.read()
            report.filename = filename
            report.mimetype = mimetype
            
            try:
                db.session.commit()
                flash('Report saved successfully', 'success')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving officer report: {str(e)}")
                flash(f'An error occurred while saving the report. Please try again.', 'danger')

        return render_template('/officer/officer-case-details.html', report=report)
    except:
        current_app.logger.error("Database error:")
        flash("An error occurred while fetching the case report details. Please try again later.", "danger")
        return redirect(url_for('officers.assignedCase'))
    
@officers.route('/officer/download-image/<int:report_id>')
@officer_required
def download_image(report_id):
    report = CaseReport.query.get_or_404(report_id)
    if not report.media:
        flash('No image found', 'danger')
        return redirect(url_for('officers.caseDetails', report_id=report_id))
    
    return Response(
        report.media,
        mimetype=report.mimetype,
        headers={
            "Content-Disposition": f"attachment;filename={report.filename}"
        }
    )
    
@officers.route('/officer/status')
@officer_required
def caseStatus():
    officer_id = session['officer_id']

    search_case_status = request.args.get('search_case_status', '')
    try:
        if search_case_status:
            case_status = CaseReport.query.filter(
                CaseReport.assigned_officer_id == officer_id
            ).filter(
                or_(
                CaseReport.location.ilike(f'%{search_case_status}%') | 
                CaseReport.status.ilike(f'%{search_case_status}%') |
                CaseReport.date.ilike(f'%{search_case_status}%') |
                CaseReport.time.ilike(f'%{search_case_status}%') |
                CaseReport.crime_type.ilike(f'%{search_case_status}%') |
                CaseReport.created_at.ilike(f'%{search_case_status}%') |
                CaseReport.urgency.ilike(f'%{search_case_status}%')
                )
            ).all()
        else:
            case_status = CaseReport.query.filter_by(assigned_officer_id=officer_id).all()
    except:
        current_app.logger.error("Database error:")
        
        flash("No report with the keyword.", "warning")
        
        return redirect(url_for('officers.caseStatus'))
        

    return render_template('/officer/case-status.html', case_status=case_status)

@officers.route('/officer/status/<int:report_id>', methods=['POST'])
@officer_required
def updateCaseStatus(report_id):
    try:
        case = CaseReport.query.get_or_404(report_id)
        case_status = request.form.get('case_status')
        if case_status:
            case.status = case_status
            db.session.commit()
            subject = f"Case Status Update"
            body = f"""
                The status of the case report (Crime: {case.crime_type}) has been updated.
                New Status: {case.status}
            """
            if send_status_admin_email(subject, body):
                flash(f'Success. Case status updated to {case_status}.', 'success')
            else:
                flash("Failed to send email notification.", "warning")
        else:
            flash('Failed to update case status.', 'danger')
    except:
        current_app.logger.error("Database error:")
        flash("An error occurred. Please try again later.", "danger")
        
    return redirect(url_for('officers.caseStatus'))

@officers.route('/officer/settled-cases')
@officer_required
def settledCase():
    officer_id = session['officer_id']
    search_settled_cases = request.args.get('search_settled_cases', '')
    try:
        if search_settled_cases:
            solved_cases = CaseReport.query.filter(
                CaseReport.assigned_officer_id == officer_id,
                CaseReport.status == 'Solved'
            ).filter(
                or_(
                CaseReport.location.ilike(f'%{search_settled_cases}%') | 
                CaseReport.status.ilike(f'%{search_settled_cases}%') |
                CaseReport.date.ilike(f'%{search_settled_cases}%') |
                CaseReport.time.ilike(f'%{search_settled_cases}%') |
                CaseReport.crime_type.ilike(f'%{search_settled_cases}%') |
                CaseReport.created_at.ilike(f'%{search_settled_cases}%') |
                CaseReport.urgency.ilike(f'%{search_settled_cases}%')
                )
            ).all()
        else:
            solved_cases = CaseReport.query.filter_by(assigned_officer_id=officer_id, status='Solved').all()
    except:
        current_app.logger.error("Database error:")
        
        flash("No report with the keyword.", "warning")
        
        return redirect(url_for('officers.settledCase'))
        
    return render_template('/officer/settled-cases.html', solved_cases=solved_cases)

@officers.route('/officer/settled-case-details/<int:report_id>', methods=['POST','GET'])
@officer_required
def settledCaseDetails(report_id):
    try:
        settled_report = CaseReport.query.get_or_404(report_id)

        if settled_report is None:
                flash("Case details not found.", "warning")
                return redirect(url_for('officers.settledCase'))

        return render_template('/officer/settled-case-details.html', settled_report=settled_report)
    except:
        current_app.logger.error("Database error:")
        flash("An error occurred while fetching the case report details. Please try again later.", "danger")
        return redirect(url_for('officers.settledCase'))
    
@officers.route('/officer/officer-reports')
@officer_required
def officerReports():
    officer_id = session['officer_id']
    try:
        my_reports = CaseReport.query.filter_by(assigned_officer_id=officer_id).all()
        
        for report in my_reports:
            if report.reports is None:
                report.plain_text = "No report for case"
            else:
                report.plain_text = BeautifulSoup(report.reports, "html.parser").get_text()
    except Exception as e:
        current_app.logger.error(f"Database error: {str(e)}")
        flash("An error occurred while fetching the case report details. Please try again later.", "danger")
        return redirect(url_for('officers.officerReports'))
    
    return render_template('officer/officer-reports.html', my_reports=my_reports)


@officers.route('/officer/officer-notification')
@officer_required
def officerNotification():
    return render_template('officer/officer-notification.html')

@officers.route('/officer/officer-setting', methods=['POST', 'GET'])
@officer_required
def officerSetting():
    officer_id = session.get('officer_id')  
    officer_profile = Officers.query.get(officer_id)
    
    if not officer_profile:
        flash("Officer details not found", "error")
        return redirect(url_for('officers.officerSetting')) 

    if request.method == 'POST':
        if 'update_profile' in request.form:
            officer_profile.first_name = request.form.get('first_name')
            officer_profile.last_name = request.form.get('last_name')
            officer_profile.username = request.form.get('username')
            officer_profile.officer_email = request.form.get('email')
            officer_profile.rank = request.form.get('rank')
            officer_profile.station = request.form.get('station')
            
            try:
                db.session.commit()
                flash("Profile updated successfully", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "error")
        
        elif 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not check_password_hash(officer_profile.password, current_password):
                flash("Current password is incorrect", "danger")
            elif new_password != confirm_password:
                flash("New passwords do not match", "danger")
            else:
                officer_profile.password = generate_password_hash(new_password)
                try:
                    db.session.commit()
                    flash("Password changed successfully", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred: {str(e)}", "error")
        
        return redirect(url_for('officers.officerSetting'))
    
    return render_template('officer/officer-setting.html', officer=officer_profile)

@officers.route('/officer/logout')
@officer_required
def officerLogout():    
    if not session.get('officer_id'):
        return redirect('/officer/login')
    if session.get('officer_id'):
        session['officer_id']=None
        session['officer_username']=None
        flash('You have been logged out.', category='info')
        logout_user()
    return redirect(url_for('officers.officerLogin'))