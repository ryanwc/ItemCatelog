# Overview

Restaurant Manager is a social website that helps restaurant staff and owners manage restaurants and their menus.

# What it Does

Restaurant Manager is an interactive website that lets you sign in with Google or Facebook and manage cuisines, cuisine "base menu items", restaurants, and restaurant menu items.

User profiles, restaurants, cuisines, base menu items, and restaurant menu items display pictures and various other attributes (like "price"), and can be created, edited, and deleted if you are logged in and have the appropriate authority.

The forms, where appropriate, provide real-time visual and textual cues about valid/invalid input, and on form submission, the browser will alert you of any invalid input so you can correct it before the form is processed.  The results of form processing are then displayed to you.

You can do the following:

- View, create, edit, and delete cuisines, cuisine base menu items, restaurants, and restaurant menu items
- View online versions of restaurant menus
- Edit your profile picture and username
- Interact with other users by sending emails

Currently, the only social interaction is through looking up user email addresses.  A messaging system between users is planned.

# Neat Tips

Cuisines have a list of "base menu items" that are associated with them, and the base menu items are distinct entities from restaurant menu items.  If you select a cuisine when creating a restaurant, the restaurant's menu will be pre-populated with instances of all of the base menu items for that cuisine.  If you wish, you can then modify or delete the restaurant menu items.  This applies to user-created cuisines and base menu items as well.  For example, if you create a cuisine named "Mexican", create a base menu item for "Mexican" named "Tacos", and then create a restaurant with cuisine "Mexican", the new restaurant's menu will be pre-populated with an instance of "Tacos" that you can then modify without affecting the base menu item "Tacos".

When creating a restaurant menu item, you must select a base menu item to base it on.  When you select an item from the dropdown, the form placeholders (including picture) will all change to reflect that base menu item's attributes.  If you do not provide a value for any form field, the restaurant menu item will default to having the attribute of it's base menu item.

Various pages have stats about their subject matter, and the stats change based on your sign-in status.  For example, if you are signed in, you will be visually alerted to which restaurants are yours and will see extra stats in your profile page.

Most of the information displayed for most pages is available in JSON format.  To access a page's JSON formatted information, simply add "/JSON" to the end of the url.

# How to Get and Use this Code

1. Download all of the files in this repo into the same directory on your computer.
2. If not already installed, download and install Python on your computer.  This was created using Python 2.7, so for best compatibility ensure you are using Python 2.7+.  I am unsure if Python 3.0+ is completely supported.
3. If not already installed, install Flask (the Python web framework) on your computer.  This app was made and tested with Flask version 0.9.  You can install the latest version by typing `pip install Flask` at the command line, or you can read further instructions [here](http://flask.pocoo.org/).
4. If not already installed, install SQLAlchemy (a database toolkit for Python).  This app was made and tested with SQLAlchemy 0.8.4.  You can view instructions for downloading and installing SQLAlchemy [here](http://www.sqlalchemy.org/download.html).
5. From the command line, navigate to the directory into which you downloaded all the files.
6. Optional (but recommended for testing): To pre-populate the database with sample restaurants, cuisines, base menu items, restaurant menu items, and users, run the command-line command `python InitPopScript.py`.  This may take 10-20 seconds to complete.
7. From the command line, run the command `python run.py`.
8. In your browser, navigate to "localhost:5000/", "localhost:5000/index", or "localhost:5000/login".  You can now sign-in with Google or Facebook to create a profile, or you can navigate the site without signing in.

# Technologies Used

- Database:			SQLite
- Server Scripting: Python 2.7
- Web Framework: 	Flask 0.9
- Browser:			HTML
- Styling:			CSS
- Interactivity:	JavaScript (and jQuery)
