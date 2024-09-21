# Import necessary modules and components
from market import app
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from market.models import Item, User, CartItem
from market.forms import RegisterForm, LoginForm
from market import db
from flask_login import login_user, logout_user, login_required, current_user
from paystackapi.transaction import Transaction
from paystackapi.paystack import Paystack
import secrets
import uuid

# Initialize Paystack API (assuming API keys are set in __init__.py)
paystack = Paystack()

# Home page route
@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/search')
def search():
    query = request.args.get('q')  # 'q' is the name of the search input field
    results = []
    
    if query:  # If there is a search term, perform the search
        # Search for items where the name matches the query (case insensitive)
        results = Item.query.filter(Item.name.ilike(f'%{query}%')).all()

    return render_template('search_result.html', query=query, results=results)

# Shop page route (requires login)
@app.route('/shop', methods=['GET', 'POST'])
def shop_page():
    items=Item.query.all()
    owned_items = []
    if current_user.is_authenticated:
        owned_items = Item.query.filter_by(owner=current_user.id).all()
    return render_template('shop.html', items=items, owned_items=owned_items)

# Add item to cart route
@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    item = Item.query.get_or_404(item_id)
    if item.owner:
        flash("This item is already owned by someone.", category="danger")
    else:
        cart_item = CartItem(user_id=current_user.id, item_id=item.id)
        db.session.add(cart_item)
        db.session.commit()
        flash(f"{item.name} has been added to your cart!", category="success")
    return redirect(url_for('shop_page'))

# Checkout page route
@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    item_id = request.args.get('item_id')
    if item_id:
        item = Item.query.get_or_404(item_id)
        total = item.price
        items = [item]
    else:
        items = current_user.cart_items()
        total = current_user.cart_total()
    return render_template('checkout.html', items=items, total=total)

# Initiate payment route
@app.route('/initiate_payment', methods=['POST'])
@login_required
def initiate_payment():
    item_data = request.get_json()
    if not item_data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    item_id = item_data.get('item_id')
    if item_id:
        item = Item.query.get_or_404(item_id)
        total_amount = item.price * 100  # Convert to kobo
    else:
        total_amount = current_user.cart_total() * 100  # Convert to kobo
    
    reference = secrets.token_hex(16)  # Generate a unique reference
    
    try:
        # Initialize Paystack transaction
        response = paystack.transaction.initialize(
            reference=reference,
            amount=total_amount,
            email=current_user.email_address,
            callback_url=url_for('payment_callback', _external=True)
        )
        
        if response['status']:
            # Store the reference and item_id (if applicable) in the session
            session['payment_reference'] = reference
            if item_id:
                session['payment_item_id'] = item_id
            
            # Return the necessary data to the frontend
            return jsonify({
                'status': 'success',
                'authorization_url': response['data']['authorization_url'],
                'reference': reference,
                'amount': total_amount,
                'email': current_user.email_address
            })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to initiate payment'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/payment_callback')
@login_required
def payment_callback():
    reference = request.args.get('reference') or session.pop('payment_reference', None)
    item_id = session.pop('payment_item_id', None)
    if not reference:
        flash("No payment reference found.", category='danger')
        return redirect(url_for('shop_page'))

    try:
        # Verify Paystack transaction
        response = paystack.transaction.verify(reference=reference)
        if response['status'] and response['data']['status'] == 'success':
            if item_id:
                # Process single item purchase
                item = Item.query.get_or_404(item_id)
                item.owner = current_user.id
                db.session.add(item)
                flash(f"Payment successful. You have purchased {item.name}!", category='success')
            else:
                # Process cart purchase
                cart_items = current_user.cart_items()
                for item in cart_items:
                    item.owner = current_user.id
                    db.session.add(item)
                
                # Clear the user's cart
                CartItem.query.filter_by(user_id=current_user.id).delete()
                
                flash("Payment successful. Your items have been purchased!", category='success')
            
            db.session.commit()
        else:
            flash("Payment was not successful. Please try again.", category='danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", category='danger')

    return redirect(url_for('shop_page'))

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('shop_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')
    return render_template('register.html', form=form)

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('shop_page'))
        else:
            flash('Incorrect Username or password! Please try again', category='danger')
    return render_template('login.html', form=form)

# User logout route
@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))