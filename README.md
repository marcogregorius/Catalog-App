# Catalog App
Catalog App is a web app that lists a catalog of sports categories and items in every category. The website is featured with authentication to authenticate real user and authorization to authorize the correct user when modifying the item. User has the option to login with traditionally entering username and password or via Google Sign In.
The website in its simplest form displays the basic CRUD functionality.

## Technology Used
- Backend: Python with Flask framework and SQL Alchemy
- Frontend: HTML5 and CSS with Bootstrap Framework

## Download
- Fork this Github [repository](https://github.com/marcogregorius/Catalog-App)
- Clone to your local repository by pasting below line into your command line:
  `https://github.com/marcogregorius/Catalog-App.git`

## Usage Instruction
### Connect to Udacity VM to run the server:
- `cd` to the `/catalog/` folder
- Run `vagrant up`
- Enter `vagrant ssh`
- In the vagrant environment, `cd` to the `/catalog/` folder.
- Run the server python file with `python project.py`

### Launch the website from your browser (Google Chrome is preferred):
- Go to http://localhost:8000
- Start with registering your account or logging in via Google Sign In
   - Registration page:
   ![alt text](/screenshots/register.png "Registration page")
   - Login page:
   ![alt text](/screenshots/login.png "Login page")
- After logged in, you will have the access to add new item as below.
   - Home page (logged in user):
   ![alt text](/screenshots/home.png "Home page")
- From here, you can navigate through your added items in "My Item" on the top right corner, as well as edit and delete your own item.
- Note that you are not authorized to edit or delete items that do not belong to you (not added by you).


