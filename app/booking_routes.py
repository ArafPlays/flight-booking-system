from flask import render_template,request,session,redirect,url_for,flash
from app import app

import random # to generate a random booking reference number

from app.models import db,Flight,Booking, Passenger


@app.route("/",methods=['GET','POST'])
def index():
    if request.method=='GET':
        all_flights = Flight.query.all()
        return render_template('index.html',all_flights=all_flights)
    elif request.method=='POST':
        # clear session first to avoid any collisions
        session.clear()

        # check if cityFrom and cityTo is same.
        if request.form['cityFrom']==request.form['cityTo']:
            # flash message and refresh if cities are same.
            flash("From and to cities must be different.")
            return redirect(url_for('index'))
        
        # check if return date comes before departure date
        if request.form['returnDate'] and request.form['departDate']>request.form['returnDate']:
            # flash message 
            flash("Depart date must come before return date.")
            return redirect(url_for('index'))
        
        # after checking, save to session
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
        flash("Sorry, no departure flight found. Change your search or create your own flight in admin panel.")
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
    session['preference'] = preference.capitalize()
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
            return_flight_num=None
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