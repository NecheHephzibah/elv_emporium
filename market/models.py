from market import db, login_manager
from market import bcrypt
from flask_login import UserMixin

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email_address = db.Column(db.String(60), nullable=False, unique=True)
    password_hash = db.Column(db.String(60), nullable=False)
    items = db.relationship('Item', backref='owned_user', lazy=True)
    cart = db.relationship('CartItem', backref='user', lazy=True)

    # Password getter (prevents direct access to password)
    @property
    def password(self):
        return self.password

    # Password setter (hashes the password before storing)
    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    # Method to check if a given password matches the hashed password
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    # Method to check if a user can purchase an item (placeholder implementation)
    def can_purchase(self, item_obj):
        # This method needs to be updated to use a different logic
        # For now, we'll assume the user can always purchase
        return True

    # Method to get all items in the user's cart
    def cart_items(self):
        return [cart_item.item for cart_item in self.cart]

    # Method to calculate the total price of items in the cart
    def cart_total(self):
        return sum(cart_item.item.price for cart_item in self.cart)

# Item model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    category = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))

    # String representation of the Item object
    def __repr__(self):
        return f"Item('{self.name}')"

    # Method to process the purchase of an item
    def buy(self, user):
        self.owner = user.id
        db.session.commit()

# CartItem model (represents items in a user's cart)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item')