# [Catalog App](http://catalog.marcogreg.com)
Catalog App is a web app that lists a catalog of sports categories and items in every category. The website is featured with authentication to authenticate real user and authorization to authorize the correct user when modifying the item. User has the option to login with traditionally entering username and password or via Google Sign In. The traditional sign in uses the feature of hashing (SHA256) a unique salt with the password and stores the hashed password in the database.
The website in its simplest form displays the basic CRUD functionality and provides API endpoints of the database.

## Technology Used
- Backend: Python with Flask framework, PostgreSQL + SQL Alchemy
- Frontend: HTML5 and CSS with Bootstrap Framework

## Usage Instruction

### - Simply visit http://catalog.marcogreg.com (Recommended)

### - Or, clone and run from your local machine (vagrant VM setup is required):
- Clone this GitHub repository by pasting below line into your terminal/command line:
  `git clone https://github.com/marcogregorius/Catalog-App.git`
- `cd` to the `/catalog/` folder
- Run `vagrant up`
- Enter `vagrant ssh`
- In the vagrant environment, `cd` to the `/catalog/` folder.
- Run the server python file with `python project.py`

### Launch the website from your browser (Google Chrome is preferred):
- Go to http://localhost:8000 (if you host locally)
- Start with registering your account or logging in via Google Sign In
   - Registration page:
   ![alt text](/screenshots/register.png "Registration page")
   - Login page - User has the option for signing in using locally created account from the registration page or via Google Sign In:
   ![alt text](/screenshots/login.png "Login page")
- After logged in, you will have the access to add new item as below.
   - Home page (logged in user):
   ![alt text](/screenshots/home.png "Home page")
- From here, you can navigate through your added items in "My Item" on the top right corner, as well as edit and delete your own item.
- Note that you are not authorized to edit or delete items that do not belong to you (not added by you).

## API Endpoints
The Catalog App also provides below API endpoints, formatted as below:

- /catalog.json

- /catalog/**category**.json
  
  _**Try**_ http://catalog.marcogreg.com/catalog/Soccer.json
  
- /catalog/**category**/**item**.json
  
  _**Try**_ http://catalog.marcogreg.com/catalog/Hockey/Puck.json

Both `category` and `item` are case-sensitive.

List of category: `Baseball, Basketball, Foosball, Frisbee, Hockey, Rock Climbing, Skating, Snowboarding, Soccer`
