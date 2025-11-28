from flask import render_template,request,redirect,url_for,flash
from app import app


import random # to generate a random booking reference number
from datetime import datetime # for working with dates and time

# imports for admin user authentication and hashing
# loginManager only handles when you're logged in/logged out and who the current logged in user is. It stores these in sessions.
from flask_login import LoginManager

from flask_login import login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt # for hashing admin password

from app.models import db,Flight,Admin

# bcrypt for hashing
bcrypt = Bcrypt(app)

# setting up loginManager (flask-login library)
login_manager = LoginManager()
login_manager.init_app(app)

# user loader (from flask-login docs)
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# flights can be added/edited/deleted to flights database on this page
@app.route("/admin",methods=['GET','POST'])
def admin():
    #  if current user is logged in, we show them the page, otherwise they'll be taken to login page
    if current_user.is_authenticated:
        if request.method=='GET':
            # get all flights so we can show them on the page
            all_flights = Flight.query.all()
            return render_template('admin.html',all_flights=all_flights)
        elif request.method=='POST':
            # if submit button is clicked, check if cityFrom and cityTo are same.
            if request.form['cityFrom']==request.form['cityTo']:
                # flash message and refresh if cities are same.
                flash("From and to cities must be different.")
                return redirect(url_for('admin'))
            
            # check if return date comes before departure date
            if request.form['departDate']>request.form['arrivalDate']:
                # flash message 
                flash("Depart date must come before arrival date.")
                return redirect(url_for('admin'))
            
            cityFrom = request.form['cityFrom']
            cityTo = request.form['cityTo']
            departDate = request.form['departDate']
            arrivalDate = request.form['arrivalDate']
            departTime = request.form['departTime']
            arrivalTime = request.form['arrivalTime']
            fclass = request.form['fclass']

            # use calculateDuration function below to calculate difference
            duration=calculateDuration(departDate,departTime,arrivalDate,arrivalTime)

            price = request.form['price']
            new_flight = Flight(cityFrom=cityFrom,cityTo=cityTo,departDate=departDate,arrivalDate=arrivalDate,departTime=departTime,arrivalTime=arrivalTime,duration=duration,fclass=fclass,price=price)
            db.session.add(new_flight)
            db.session.commit()
            
            flash("Flight added successfully.")
            # refresh the page
            return redirect(url_for('admin'))
    else:
        flash("Please login or create account to access admin panel")
        return redirect(url_for('login'))

# delete a flight from admin panel
@app.route('/admin/delete/<int:num>')
@login_required # protects these pages from being accessed by unauthenticated people
def delete(num):
    flight_to_delete = Flight.query.filter_by(num=num).first()
    if flight_to_delete:
        db.session.delete(flight_to_delete)
        db.session.commit()
        return redirect(url_for('admin'))
    else:
        return "Flight doesn't exist"
    
# used when creating and editing flights (admin and edit functions/pages).
def calculateDuration(departDate,departTime,arrivalDate,arrivalTime):
    depart = departDate + " " + departTime
    depart = datetime.strptime(depart,"%Y-%m-%d %H:%M")

    arrival = arrivalDate + " " + arrivalTime
    arrival = datetime.strptime(arrival,"%Y-%m-%d %H:%M")

    duration = arrival-depart
    return duration


# edit a flight from admin panel
@app.route('/admin/edit/<int:num>',methods=['GET','POST'])
@login_required # protects these pages from being accessed by unauthenticated people
def edit(num):
    flight_to_edit = Flight.query.filter_by(num=num).first()
    if flight_to_edit:
        if request.method=='GET':
            return render_template('edit.html',flight_to_edit=flight_to_edit)
        elif request.method=='POST':
            # if submit button is clicked, check if cityFrom and cityTo are same.
            if request.form['cityFrom']==request.form['cityTo']:
                # flash message and refresh if cities are same.
                flash("From and to cities must be different.")
                return redirect(url_for('edit',num=num))
            
            # check if return date comes before departure date
            if request.form['departDate']>request.form['arrivalDate']:
                # flash message 
                flash("Depart date must come before arrival date.")
                return redirect(url_for('edit',num=num))
            
            # edit database when user submits edit form and checks are done
            flight_to_edit.cityFrom=request.form['cityFrom']
            flight_to_edit.cityTo=request.form['cityTo']
            flight_to_edit.departDate=request.form['departDate']
            flight_to_edit.arrivalDate=request.form['arrivalDate']
            flight_to_edit.departTime=request.form['departTime']
            flight_to_edit.arrivalTime=request.form['arrivalTime']
            flight_to_edit.fclass=request.form['fclass']
            flight_to_edit.price=request.form['price']

            # use calculateDuration function below to calculate difference
            flight_to_edit.duration=calculateDuration(flight_to_edit.departDate,flight_to_edit.departTime,flight_to_edit.arrivalDate,flight_to_edit.arrivalTime)
            
            db.session.commit()
            flash("Changes saved.")
            return redirect(url_for('admin'))
    else:
        return "Flight doesn't exist"

# create new admin account
@app.route('/admin/create',methods=['GET','POST'])
def create():
    # if user is already logged in, take them back to admin page
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('admin'))
    else:
        if request.method=='GET':
            return render_template('create.html')
        elif request.method=='POST':
            # get username and pass that user
            username=request.form['username']
            password=request.form['password']

            # if username already exists, flash a message and redirect to create account page
            if Admin.query.filter_by(username=username).first():
                flash("Username already exists")
                return redirect(url_for('create'))
            
            # generate hash from password using bcrypt
            hash = bcrypt.generate_password_hash(password).decode('utf-8')
            # add new admin to database
            # we store the hash, not the password. So if database is leaked, passwords are safe.
            new_admin = Admin(username=username,hash=hash)
            db.session.add(new_admin)
            db.session.commit()
            # take them to login page after user has been created
            flash("Account created successfully.")
            return redirect(url_for('login'))

# login to existing admin account
@app.route('/admin/login',methods=['GET','POST'])
def login():
    # if user is already logged in, take them back to admin page
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('admin'))
    else:
        if request.method=='GET':
            return render_template('login.html')
        elif request.method=='POST':
            username=request.form['username']
            password=request.form['password']
            # generating hash again and checking doesnt work because bcrypt automatically adds a random salt,so the hashes dont match
            # we need to use check_password_hash instead
            admin = Admin.query.filter_by(username=username).first()
            # check if user provided password's hash and database stored hash matches
            if admin and bcrypt.check_password_hash(admin.hash,password):
                # using built in flask-login library functions to login the admin
                login_user(admin)
                flash('Successfully logged in')
                return redirect(url_for('admin'))
            else:
                flash("Incorrect credentials!")
                return redirect(url_for('login'))

@app.route('/admin/logout')
def logout():
    # built in logout_user function by flask-login
    logout_user()
    flash('Successfully logged out.')
    return redirect(url_for('login'))
    
