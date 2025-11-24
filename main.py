from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import datetime
import random # to generate a random booking reference number

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

    booking = db.relationship('Booking',secondary=booking_passenger,backref='passengers')
    # due to backref, both passenger.bookings and booking.passengers have been created.

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

    # specifying foreign keys
    depart_flight=db.relationship('Flight',foreign_keys=[depart_flight_num],backref='depart_bookings')
    return_flight=db.relationship('Flight',foreign_keys=[return_flight_num],backref='return_bookings')
    # backref automatically gives us access to flight.departure_bookings and flight.return_bookings

    # store booking preferences
    meal=db.Column('meal',db.String(10),nullable=False)
    seat=db.Column('seat',db.String(3),nullable=False)
    email=db.Column('email',db.String(15),nullable=False)
    phone=db.Column('phone',db.String(15),nullable=False)
    # booking reference (used for verification before viewing and managing and viewing bookings)
    ref = db.Column('ref',db.Integer,nullable=False)
@app.route("/",methods=['GET','POST'])
def index():
    if request.method=='GET':
        return render_template('index.html')
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
    matching_flights = Flight.query.filter_by(cityFrom=session['cityFrom'],cityTo=session['cityTo'],departDate=session['departDate'],fclass=session['fclass'])
    return render_template('departure.html',matching_flights=matching_flights)

@app.route("/return-flight")
def return_flight():
    # flip cityTo and cityFrom
    cityTo = session['cityFrom'] 
    cityFrom = session['cityTo'] 
    returnDate=session['returnDate']
    fclass=session['fclass']
    # query flights database and show flights that match
    # this flight will depart on the user selected return date
    matching_flights = Flight.query.filter_by(cityFrom=cityFrom,cityTo=cityTo,departDate=returnDate,fclass=fclass)
    return render_template('departure.html',matching_flights=matching_flights)

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

@app.route("/seat")
def seat():
    chosenSeat = request.args['chosenSeat']
    return render_template('seat.html',chosenSeat=chosenSeat)

@app.route("/save-seat/<chosenSeat>")
def save_seat(chosenSeat):
    # save seat to session
    session['chosenSeat'] = chosenSeat
    
    # return f"{session['chosenSeat']}"

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
        # get meal and seat number
        # preference = session['preference']
        # chosenSeat = session['chosenSeat']
        # passing session automatically sends all session data, no need to create variables and send individually
        return render_template('payment.html',flight=flight,session=session)
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
    
@app.route("/manage/<int:booking_id>/<int:booking_ref>")
def manage(booking_id,booking_ref):
    # get the booking
    booking = Booking.query.filter_by(id=booking_id).first()
    # booking.ref is the actual ref, booking_ref is user provided. We check if they match.
    if booking.ref == booking_ref:
        return render_template('manage.html',booking=booking)
    return f"Booking id or reference isn't correct"

# flights can be added/edited/deleted to flights database on this page
@app.route("/admin",methods=['GET','POST'])
def admin():
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
        # refresh the page
        return redirect(url_for('admin'))

# delete a flight from admin panel
@app.route('/admin/delete/<int:num>')
def delete(num):
    flight_to_delete = Flight.query.filter_by(num=num).first()
    db.session.delete(flight_to_delete)
    db.session.commit()
    return redirect(url_for('admin'))

# edit a flight from admin panel
@app.route('/admin/edit/<int:num>',methods=['GET','POST'])
def edit(num):
    if request.method=='GET':
        flight_to_edit = Flight.query.filter_by(num=num).first()
        return render_template('edit.html',flight_to_edit=flight_to_edit)
    elif request.method=='POST':
        flight_to_edit = Flight.query.filter_by(num=num).first()
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

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=8000,debug=True)