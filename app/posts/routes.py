from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.posts.models import Crime, Theft
from app import db

posts = Blueprint('posts', __name__)

@posts.route('/theft_report', methods=['GET', 'POST'])
def report_theft():   
    if request.method == 'POST':
        place_of_theft = request.form.get('place_of_theft')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        date_of_theft = request.form.get('date_of_theft')
        phone_number = request.form.get('phone_number')
        value = request.form.get('value')
        time_of_theft = request.form.get('time_of_theft')
        stolen_property = request.form.get('stolen_property')
        description = request.form.get('description')

        theft_report = Theft(place_of_theft=place_of_theft, 
                                street_address=street_address,
                                city=city, 
                                date_of_theft=date_of_theft,
                                phone_number=phone_number, 
                                value=value,
                                time_of_theft=time_of_theft, 
                                stolen_property=stolen_property,
                                description=description)
        db.session.add(theft_report)
        db.session.commit()
        flash(f"Your theft report was sent successfully", category='success')
        return redirect(url_for('users.user_dashboard'))
    return render_template('user/report_theft.html')


@posts.route('/crime_report', methods=['GET', 'POST'])
def report_crime():
    if request.method == 'POST':
        date_of_incident = request.form.get('date_of_incident')
        issued_by = request.form.get('issued_by')
        time_of_incident = request.form.get('time_of_incident')
        incident_location = request.form.get('incident_location')
        incident_nature = request.form.get('incident_nature')
        incident_details = request.form.get('incident_details')
        suspect_details = request.form.get('suspect_details')
        arrest_history = request.form.get('arrest_history')
        suspect_name = request.form.get('suspect_name')
        comments = request.form.get('comments')

        if request.files:
            file_upload = request.files['file_upload']
            file_content = file_upload.read()  # Read file content as bytes
        else:
            file_upload = None
            file_content = None  # Set to None if no file uploaded

        crime_report = Crime(date_of_incident=date_of_incident, 
                                issued_by=issued_by,
                                time_of_incident=time_of_incident, 
                                incident_location=incident_location,
                                incident_nature=incident_nature, 
                                incident_details=incident_details,
                                suspect_details=suspect_details, 
                                arrest_history=arrest_history,
                                suspect_name=suspect_name,
                                comments=comments,
                                file_upload=file_content
                                )
        try:
            db.session.add(crime_report)
            db.session.commit()
            flash(f"Your crime report was sent successfully", category='success')
            return redirect(url_for('users.user_dashboard'))
        except Exception as e:
            # Handle database errors gracefully (e.g., log the error)
            flash(f"An error occurred: {str(e)}", category='error')
            return render_template('user/report_crime.html')
    return render_template('user/report_crime.html')