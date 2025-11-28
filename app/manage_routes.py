from flask import render_template,request,redirect,url_for,flash
from app import app

from app.models import db,Booking

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
            # after deleting booking, send them to homepage with a flash message.
            flash("Successfully deleted booking and passenger records.")
            return redirect(url_for('index'))
        else:
            return f"Booking id or reference isn't correct"
    except Exception as e:
        return f"Sorry, error occured: {e}"