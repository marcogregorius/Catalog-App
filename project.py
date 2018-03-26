from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import datetime
import uuid
import hashlib
from functools import wraps

app = Flask(__name__)

engine = create_engine('sqlite:///catalognew.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    """
    Login page - User can choose between manually logging in with the registered username & password or with Google Sign-in
    """
    if request.method == 'POST':
        # When pressing submit button, do the following.
        if request.form['submit'] == 'submit':
            username = request.form['username']
            password = request.form['password']

            # Check if the username exists
            username_exists = session.query(User).filter_by(username=username).first()
            if not username_exists:
                return render_template('login_username_does_not_exist.html')

            # Check if password is correct. If correct, redirected to home with storing the necessary login_session informations.
            if check_password(username, password):
                login_session['username'] = username
                email = session.query(User).filter_by(username=username).one().email
                user_id = session.query(User).filter_by(username=username).one().id
                login_session['email'] = email
                login_session['provider'] = 'manual'
                login_session['user_id'] = user_id
                login_session['picture'] = 'NA'
                return redirect(url_for('home'))
            else:
                return render_template('login_wrong_password.html')

        # When pressing cancel button, redirected to home page.
        if request.form['submit'] == 'cancel':
            return redirect(url_for('home'))

    # If user clicks Google Login, pass the token in state variable.
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration page - User can register by inputting username, password, email and real name.
    """
    if request.method == 'POST':
        if request.form['submit'] == 'submit':
            username = request.form['username']
            email = request.form['email']
            username_exists = session.query(User).filter_by(username=username).first()
            email_exists = session.query(User).filter_by(email=email).first()
            if username_exists:
                return render_template('register_user_already_exists.html')
            if email_exists:
                return render_template('register_email_already_exists.html')
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            hashed_password, salt = hash_password(password)
            new_user = User(username=username, name=name, email=email, salt=salt, hashed_password=hashed_password)
            session.add(new_user)
            session.commit()
            user_id = session.query(User).filter_by(username=username).one().id
            login_session['username'] = username
            login_session['email'] = email
            login_session['provider'] = 'manual'
            login_session['user_id'] = user_id
            login_session['picture'] = 'NA'
            return redirect(url_for('home'))
        if request.form['submit'] == 'cancel':
            return redirect(url_for('home'))
    else:
        return render_template('register.html')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


def createUser(login_session):
    newUser = User(username=login_session['email'], name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def hash_password(password):
    """
    Generate a unique salt for every password then hash the password.
    """
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest(), salt


def check_password(username, password):
    """
    Check current username's password from the hashed password in the database
    This function will hash the password first before matching to the one in the database
    """
    user = session.query(User).filter_by(username=username).one()
    hashed_password = hashlib.sha256(user.salt.encode() + password.encode()).hexdigest()
    return hashed_password == user.hashed_password

def login_required(function):
    @wraps(function)
    def wrapper():
        if 'username' in login_session:
            return function()
        else:
            flash('A user must be logged to add a new item.')
            return redirect(url_for('home'))
    return wrapper


@app.route('/catalog.json')
def catalogJSON():
    """
    API Endpoint for returning JSON object
    """
    categories = session.query(Category).all()
    catalog = []
    for c in categories:
        items = session.query(Item).filter_by(category_id=c.id).all()
        c = c.serialize
        catalog.append(c)
        if items:
            c['items'] = [i.serialize for i in items]
    return jsonify(Category=catalog)


@app.route('/')
@app.route('/catalog')
def home():
    """
    Listing the categories and items sorted by the creation time of the item.
    If user is not logged in, they are not allowed to add a new item.
    """
    categories = session.query(Category).order_by(Category.name).all()
    latest_items = session.query(Item).order_by(desc(Item.added_time)).all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.name
    if 'username' not in login_session:
        return render_template('publichome.html', categories=categories, latest_items=latest_items, categories_dict=categories_dict)
    else:
        return render_template('home.html', categories=categories, latest_items=latest_items, categories_dict=categories_dict,
                               username=login_session['username'])


@app.route('/<username>/items')
def myitems(username):
    """
    When user is logged in, the user's added items are shown.
    """
    categories = session.query(Category).order_by(Category.name).all()
    user_id = session.query(User).filter_by(email=login_session['email']).one().id
    my_items = session.query(Item).filter_by(user_id=user_id).all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.name
    return render_template('myitems.html', categories=categories, my_items=my_items, categories_dict=categories_dict, username=username)


@app.route('/catalog/<category>/items')
def items_in_category(category):
    """
    When a category is clicked, the items in the respective category are listed.
    If user is not logged in, adding of new item is not available.
    """
    category_id = session.query(Category).filter_by(name=category).one().id
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).filter_by(category_id=category_id).all()
    num_of_items = session.query(Item).filter_by(category_id=category_id).count()
    if 'username' not in login_session:
        return render_template('publicitems.html', categories=categories, items=items, current_category=category, num_of_items=num_of_items)
    else:
        return render_template('items.html', categories=categories, items=items, current_category=category, num_of_items=num_of_items,
                               username=login_session['username'])


@app.route('/catalog/<category>/<item>')
def item_description(category, item):
    """
    When clicking on an item, it displays the description of the item while having the option to edit/delete it.
    If user is not logged in, editing and deleting is not available.
    """
    category_id = session.query(Category).filter_by(name=category).one().id
    item = session.query(Item).filter_by(category_id=category_id, name=item).one()
    creator_name = session.query(User).filter_by(id=item.user_id).one().name
    if 'username' not in login_session:
        return render_template('publicdescription.html', item=item, category=category, creator_name=creator_name)
    else:
        return render_template('description.html', item=item, category=category, creator_name=creator_name)


@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
def new_item():
    """
    Create new item.
    """
    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'POST':
        creation_time = datetime.datetime.now()
        category_id = session.query(Category).filter_by(name=request.form['category']).one().id
        new_item = Item(name=request.form['name'], description=request.form['description'],
                        user_id=login_session['user_id'], category_id=category_id, added_time=creation_time)
        session.add(new_item)
        session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('newitem.html', categories=categories)


@app.route('/catalog/<category>/<item>/edit', methods=['GET', 'POST'])
def edit_item(category, item):
    """
    Page is only available to authorized user, ie the author of the item (who added the item).
    Authorized user is able to edit the name, description and category of the item.
    """
    if 'username' not in login_session:
        return redirect('/login')
    category_id = session.query(Category).filter_by(name=category).one().id
    item = session.query(Item).filter_by(category_id=category_id, name=item).one()
    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()'>"
        return render_template('edititem.html', category=category, item=item, categories=categories, default_category=default_category)
    categories = session.query(Category).order_by(Category.name).all()
    default_category = category
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            edited_category_id = session.query(Category).filter_by(name=request.form['category']).one().id
            item.category_id = edited_category_id
        session.commit()
        return redirect(url_for('items_in_category', category=category))
    else:
        return render_template('edititem.html', category=category, item=item, categories=categories, default_category=default_category)


@app.route('/catalog/<category>/<item>/delete', methods=['GET', 'POST'])
def delete_item(category, item):
    """
    Page is only available to authorized user, ie the author of the item who added the item.
    Authorized user is able to delete the item.
    """
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(name=item).one()
    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete this item.');}</script><body onload='myFunction()'>"
    category_id = session.query(Category).filter_by(name=category).one().id
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('items_in_category', category=category))
    else:
        return render_template('deleteitem.html', category=category, item=item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
