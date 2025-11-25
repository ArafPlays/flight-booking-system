from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

import random # to generate a random booking reference number

# imports for admin user authentication and hashing
# loginManager only handles when you're logged in/logged out and who the current logged in user is. It stores these in sessions.
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt # for hashing admin password

app=Flask(__name__)
app.secret_key = "^@^$Lrj$@$JJ223828AJEJA2828$"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fda.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db=SQLAlchemy(app)

# convention class naming is uppercase. However, sqlite stores table name in lowercase
# in this case, table name is flight.
class Flight(db.Model):
    # Note: When primary_key=True and the type is Integer, SQLAlchemy + the database automatically treat it as auto-increment. We don't need to pass in any num.
    num = db.Column("num",db.Integer, primary_key=True)
    cityFrom = db.Column("cityFrom",db.String(10), nullable=False)
    cityTo = db.Column("cityTo",db.String(10), nullable=False)
    departDate=db.Column("departDate",db.String(10), nullable=False)
    arrivalDate=db.Column("arrivalDate",db.String(10), nullable=False)
    departTime = db.Column("departTime",db.String(10), nullable=False)
    arrivalTime= db.Column("arrivalTime",db.String(10), nullable=False)
    duration= db.Column("duration",db.String(10), nullable=False)
    fclass = db.Column("fclass",db.String(10), nullable=False)
    price= db.Column("price",db.Integer, nullable=False)

# note: many to many relationships require an association table. Each pssenger can have multiple bookings and each booking can have multiple passengers.
booking_passenger=db.Table('booking_passenger',
    db.Column('booking_id',db.Integer,db.ForeignKey('booking.id')),
    db.Column('passenger_id',db.Integer,db.ForeignKey('passenger.id'))
)

class Passenger(db.Model):
    id=db.Column('id',db.Integer,primary_key=True)
    title = db.Column("title",db.String(5),nullable=False)
    fname = db.Column("fname",db.String(10),nullable=False)
    lname = db.Column("lname",db.String(10),nullable=False)
    nationality=db.Column("nationality",db.String(10),nullable=False)
    gender=db.Column("gender",db.String(10),nullable=False)

    # due to backref, both passenger.bookings and booking.passengers have been created.
    # association table is used for many to many relationship
    # because of backref, we can access xbooking.passengers and get a list of all the passengers on xbooking.
    booking = db.relationship('Booking',secondary=booking_passenger,backref='passengers')
    
class Booking(db.Model):
    # booking id
    id=db.Column('id',db.Integer,primary_key=True)

    # store passenger and flight
    # not needed anymore because we have backref on passenger table
    # passenger_id=db.Column(db.Integer,db.ForeignKey('passenger.id'), nullable=False)

    depart_flight_num=db.Column(db.Integer,db.ForeignKey('flight.num'),nullable=False)
    # using 2 foreign key to same key will cause an error here, 
    # we need to specify
    return_flight_num=db.Column(db.Integer,db.ForeignKey('flight.num'),nullable=False) # nullable false because it has to be 0 (no return) or a flight id

    # store booking preferences
    meal=db.Column('meal',db.String(10),nullable=False)
    seat=db.Column('seat',db.String(3),nullable=False)
    email=db.Column('email',db.String(15),nullable=False)
    phone=db.Column('phone',db.String(15),nullable=False)
    # booking reference (used for verification before viewing and managing and viewing bookings)
    ref = db.Column('ref',db.Integer,nullable=False)

# UserMixin is a helper class provided by Flask-Login that gives your user model all the methods and properties Flask-Login expects.
# it provides properties like is_authenticated
class Admin(db.Model,UserMixin):
    id = db.Column('id',db.Integer,primary_key=True)
    username = db.Column('username',db.String(10),nullable=False,unique=True)
    # bcrypt character is 60 characters
    hash=db.Column('hash',db.String(60),nullable=False)

@app.route("/",methods=['GET','POST'])
def index():
    if request.method=='GET':
        all_flights = Flight.query.all()
        return render_template('index.html',all_flights=all_flights)
    elif request.method=='POST':
        # clear session first to avoid any collisions
        session.clear()
        # if submit button is clicked, save to session
        session['cityFrom'] = request.form['cityFrom']
        session['cityTo'] = request.form['cityTo']
        session['departDate'] = request.form['departDate']
        session['returnDate'] = request.form['returnDate']
        session['fclass'] = request.form['fclass']
        session['passenger_num'] = int(request.form['passenger_num'])
        # send user to departure page with url query parameters
        return redirect(url_for('departure'))
    
@app.route("/departure")
def departure():
    # query flights database and show flights that match
    matching_flights = Flight.query.filter_by(cityFrom=session['cityFrom'],cityTo=session['cityTo'],departDate=session['departDate'],fclass=session['fclass']).all()
    if matching_flights:
        return render_template('departure.html',matching_flights=matching_flights)
    else:
        flash("Sorry, no departure flight found. Change your search or create your own flight in admin panel (for testing).")
        return redirect(url_for('index'))
    
@app.route("/return-flight")
def return_flight():
    # flip cityTo and cityFrom
    cityTo = session['cityFrom'] 
    cityFrom = session['cityTo'] 
    returnDate=session['returnDate']
    fclass=session['fclass']
    # query flights database and show flights that match
    # this flight will depart on the user selected return date
    matching_flights = Flight.query.filter_by(cityFrom=cityFrom,cityTo=cityTo,departDate=returnDate,fclass=fclass).all()
    if matching_flights:
        return render_template('departure.html',matching_flights=matching_flights)
    else:
        flash("Sorry, no return flight found. Change your search or create your own flight in admin panel (for testing).")
        return redirect(url_for('index'))

# this function saves both selected departing and returning flight. Saves space rather than having 2 separate functions
@app.route("/save_flight/<int:num>")
def save_flight(num):
    # first figure out if it is depart or return flight
    # if session['num'] exists, departing flight has been selected, so we book return flight 
    if 'num' in session:
        session['return_num'] = num
    # if session['num'] doesn't exist, departing flight has not been selected, so we book departing flight first 
    else:
        session['num'] = num
        if session['returnDate']!="":
            # if there's a return date, take them to select return flight selection page
            return redirect(url_for('return_flight'))
    # take them to personal details page if return flight has been saved
    return redirect(url_for('personal_details'))

@app.route("/personal-details",methods=['GET','POST'])
def personal_details():
    passenger_num=session['passenger_num']
    if request.method=='GET':
        return render_template('personal-details.html',passenger_num=passenger_num)
    elif request.method=='POST':
        # if user submits, save info to session
        # loop to go through multiple passengers
        for p in range(passenger_num):
            p = str(p)
            session['title'+p] = request.form['title'+p]
            session['fname'+p] = request.form['fname'+p] 
            session['lname'+p] = request.form['lname'+p] 
            session['nationality'+p] = request.form['nationality'+p] 
            session['gender'+p] = request.form['gender'+p] 

        session['email'] = request.form['email']
        session['phone'] = request.form['phone']
        # redirect to next page of wizard
        return redirect(url_for("seat",chosenSeat='NA'))

# we currently only have 1 type of plane, so 1 seat layout.
# when we have multiple planes, seat info needs to be stored in a new plane table.
# we currently don't verify seat selection in database. This means 2 people can book the same seat on the same flight. This needs to be fixed in future updates.
@app.route("/seat")
def seat():
    # seat selection url paramter is sent by JavaScript (seat.js)
    chosenSeat = request.args['chosenSeat']
    return render_template('seat.html',chosenSeat=chosenSeat)

@app.route("/save-seat/<chosenSeat>")
def save_seat(chosenSeat):
    # save seat to session
    session['chosenSeat'] = chosenSeat

    # redirect to next page
    return redirect(url_for('meal'))

@app.route("/meal")
def meal():
    return render_template('meal.html')

@app.route("/meal/<preference>")
def save_meal(preference):
    # save meal to session
    session['preference'] = preference
    # redirect to next page
    return redirect(url_for('payment'))

@app.route("/payment",methods=['GET','POST'])
def payment():
    if request.method=='GET':
        # get flight info
        flight_num = session['num']
        flight = Flight.query.filter_by(num=flight_num).first()

        if session['returnDate'] != "":
            return_num = session['return_num']
            return_flight = Flight.query.filter_by(num=return_num).first()
        else:
            return_flight=0
        
        return render_template('payment.html',flight=flight,return_flight=return_flight)
        
    elif request.method=='POST':
        # save to database
        
        # add new booking to database
        depart_flight_num=session['num']
        preference = session['preference']
        chosenSeat = session['chosenSeat']
        email=session['email']
        phone=session['phone']

        # if return date was kept empty, return flight number will be 0
        if session['returnDate'] =="":
            return_flight_num=0
        else:
            # if return date wasn't empty, customer will have already selected and saved a return flight number into session, we simply access and store it into a variable
            return_flight_num=session['return_num']

        booking_ref = random.randint(100,10000)
        new_booking = Booking(depart_flight_num=depart_flight_num,return_flight_num=return_flight_num,meal=preference,seat=chosenSeat,email=email,phone=phone,ref=booking_ref)
        db.session.add(new_booking)
        db.session.commit()
        passenger_num=session['passenger_num']
        # list to store all passenger ids so we can add them to booking table
        # for loop to add all passengers to database
        for p in range(passenger_num):
            p=str(p)
            title= session['title'+p]
            fname = session['fname'+p]
            lname = session['lname'+p] 
            nationality=session['nationality'+p]
            gender=session['gender'+p]
            # Note: When primary_key=True and the type is Integer, SQLAlchemy + the database automatically treat it as auto-increment. We don't need to pass in any passenger id
            new_passenger = Passenger(title=title,fname=fname,lname=lname,nationality=nationality,gender=gender)
            # video tutorial for many to many relationship: https://www.youtube.com/watch?v=47i-jzrrIGQ
            # we append the booking into passenger, this automatically updates the association table.
            new_passenger.booking.append(new_booking)
            db.session.add(new_passenger)
            db.session.commit()

        # clear session after everything has been saved to database
        session.clear()
        return redirect(url_for('confirmed',booking_id=new_booking.id,booking_ref=new_booking.ref))

@app.route("/confirmed/<int:booking_id>/<int:booking_ref>")
def confirmed(booking_id,booking_ref):
    # get the booking, flight and passenger associated with this booking id.
    booking=Booking.query.filter_by(id=booking_id).first()
    if booking.ref == booking_ref:
        depart_flight_num=booking.depart_flight_num
        depart_flight = Flight.query.filter_by(num=depart_flight_num).first()
        return_flight_num=booking.return_flight_num
        return_flight = Flight.query.filter_by(num=return_flight_num).first()
        passenger_list = booking.passengers
        return render_template('confirmed.html',booking=booking,depart_flight=depart_flight,return_flight=return_flight,passengers=passenger_list)
    else:
        return "Booking reference number isn't correct."

# this page will ask for booking id and reference number to allow access to booking.
@app.route("/manage-form", methods=['GET','POST'])
def manage_form():
    if request.method=='GET':
        return render_template('manage-form.html')
    if request.method=='POST':
        booking_id=request.form['booking_id']
        booking_ref=request.form['booking_ref']
        return redirect(url_for('manage',booking_id=booking_id,booking_ref=booking_ref))
    
@app.route("/manage/<int:booking_id>/<int:booking_ref>",methods=['GET','POST'])
def manage(booking_id,booking_ref):
    if request.method=='GET':
        # get the booking
        booking = Booking.query.filter_by(id=booking_id).first()
        # booking.ref is the actual ref, booking_ref is user provided. We check if they match.
        # check if booking actually exists and then check ref
        if booking and booking.ref == booking_ref:
            passengers = booking.passengers
            return render_template('manage.html',booking=booking,passengers=passengers)
        flash("Booking id or reference isn't correct")
        return redirect(url_for('manage_form'))
    elif request.method=='POST':
        booking = Booking.query.filter_by(id=booking_id).first()
        # get new info from input tags and update table
        # update passenger rows, need a loop here since we have multiple passengers.
        passengers = booking.passengers
        for p in passengers:
            p.fname=request.form['fname'+str(p.id)]
            p.lname=request.form['lname'+str(p.id)]

        # update booking table (meal,email,phone)
        booking.meal=request.form['meal']
        booking.email=request.form['email']
        booking.phone=request.form['phone']
        db.session.commit()
        # update booking and passenger table details to new info
        flash('Changes saved!')
        return redirect(url_for('manage',booking_id=booking_id,booking_ref=booking_ref))

@app.route("/cancel/<int:booking_id>/<int:booking_ref>")
def cancel(booking_id,booking_ref):
    try:
        # get the booking
        booking = Booking.query.filter_by(id=booking_id).first()
        # booking.ref is the actual ref, booking_ref is user provided. We check if they match.
        if booking.ref == booking_ref:
            passengers = booking.passengers
            # delete booking and associated passenger rows.
            db.session.delete(booking)
            # delete from list of passengers
            for p in passengers:
                db.session.delete(p)
            db.session.commit()
            return "Deleted booking and passenger records!"
        else:
            return f"Booking id or reference isn't correct"
    except Exception as e:
        return f"Sorry, error occured: {e}"


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
            cityFrom = request.form['cityFrom']
            cityTo = request.form['cityTo']
            departDate = request.form['departDate']
            arrivalDate = request.form['arrivalDate']
            departTime = request.form['departTime']
            arrivalTime = request.form['arrivalTime']
            fclass = request.form['fclass']
            duration = request.form['duration']
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

# edit a flight from admin panel
@app.route('/admin/edit/<int:num>',methods=['GET','POST'])
@login_required # protects these pages from being accessed by unauthenticated people
def edit(num):
    flight_to_edit = Flight.query.filter_by(num=num).first()
    if flight_to_edit:
        if request.method=='GET':
            return render_template('edit.html',flight_to_edit=flight_to_edit)
        elif request.method=='POST':
            # edit database when user submits edit form
            flight_to_edit.cityFrom=request.form['cityFrom']
            flight_to_edit.cityTo=request.form['cityTo']
            flight_to_edit.departDate=request.form['departDate']
            flight_to_edit.arrivalDate=request.form['arrivalDate']
            flight_to_edit.departTime=request.form['departTime']
            flight_to_edit.arrivalTime=request.form['arrivalTime']
            flight_to_edit.fclass=request.form['fclass']
            flight_to_edit.duration=request.form['duration']
            flight_to_edit.price=request.form['price']
            db.session.commit()
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
    
if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')