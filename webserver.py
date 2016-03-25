from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# import common gateway interface
import cgi

import RestaurantManager
from database_setup import Base, Restaurant, MenuItem

import bleach
import re

# handler -- specify what to do based on type of request
class webserverHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/restList"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1>List of All Restaurants</h1>"

                restaurants = RestaurantManager.getRestaurants()

                for restaurant in restaurants:
                    output += "<p>"
                    output += restaurant.name+" (ID "+str(restaurant.id)+")"
                    output += "<br>"
                    output += "<a href=/"
                    output += str(restaurant.id)
                    output += "restEdit>Edit</a>"
                    output += " | "
                    output += "<a href=/"
                    output += str(restaurant.id)
                    output += "restDelete>Delete</a>"
                    output += "</p>"
                
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return
            if self.path.endswith("/restAdd"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurants = RestaurantManager.getRestaurants()
                popCuisines = RestaurantManager.getPopularCuisines()

                output = ""
                output += "<html><body>"
                output += "<h1>Enter a New Restaurant into the Database</h1>"
                output += "<form name='addRest' method='POST' "
                output += "enctype='multipart/form-data'>"
                output += "<h3>Name of Restaurant</h3>"
                output += "Enter the name of the resaurant here:<br>"
                output += "<input name='name' type='text' size='50'><br>"
                
                output += "<h3>Type of Cuisine</h3>"
                output += "<input name='commOrCust' type='radio' value='common'>"
                output += " Use common cuisine from the provided list<br>"
                output += "<input name='commOrCust' type='radio' value='custom'>"
                output += " Use custom cuisine typed into the box below<br>"
                output += "<br>"
                output += "Common cuisines (based on existing restaurants):<br>"

                for cuisine in popCuisines:
                    output += "<input type='radio' name='cuisine' value='"
                    output += cuisine.foodType+"'> "+cuisine.foodType+"<br>"
                
                output += "<br>Enter custom cuisine here:<br>"
                output += "<input name='custCuisine' type='text' size='50'><br>"
                
                output += "<br><input type='submit' value='Submit Restaurant'>"
                output += "</form>"
                output += "</body></html>"
                self.wfile.write(output)
                print output
            if self.path.endswith("restEdit"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                localPath = re.search('/[0-9]+restEdit',\
                                      str(self.path)).group(0)
                rest_id = re.search('[0-9]+',localPath).group(0)
                restaurant = RestaurantManager.getRestaurant(int(rest_id))
                
                popCuisines = RestaurantManager.getPopularCuisines()

                output = ""
                output += "<html><body>"
                output += "<h1>Edit Restaurant %s</h1>" % rest_id
                output += "<form name='editRest' method='POST' "
                output += "enctype='multipart/form-data'>"
                output += "<h3>Edit Name of Restaurant</h3>"
                output += "Current name: <em>" + restaurant.name
                output += "</em><br><br>"
                output += "Enter a new name for the resaurant here:<br>"
                output += "<input name='name' type='text' size='50'><br>"
                
                output += "<h3>Edit Type of Cuisine</h3>"
                output += "Current cuisine: <em>" + restaurant.foodType
                output += "</em><br><br>"
                output += "<input name='commOrCust' type='radio' value='common'>"
                output += " Use common cuisine from the provided list<br>"
                output += "<input name='commOrCust' type='radio' value='custom'>"
                output += " Use custom cuisine typed into the box below<br>"
                output += "<br>"
                output += "Common cuisines (based on existing restaurants):<br>"

                for cuisine in popCuisines:
                    output += "<input type='radio' name='cuisine' value='"
                    output += cuisine.foodType+"'> "+cuisine.foodType+"<br>"
                
                output += "<br>Enter custom cuisine here:<br>"
                output += "<input name='custCuisine' type='text' size='50'><br>"
                
                output += "<br><input type='submit' value='Edit Restaurant'>"
                output += "</form>"
                output += "</body></html>"
                self.wfile.write(output)
                print output
        except IOError:
            self.send_error(404, "File Not Found %s" % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.end_headers()

            # parse an html header into a main value and a dictionary of params
            ctype, pdict = cgi.parse_header(self.headers.\
                                            getheader('content-type'))

            # check if the data is form data, do the post if so
            if ctype == 'multipart/form-data':
                formInfo = cgi.parse_multipart(self.rfile, pdict)

                localPath = ""
                rest_id = ""
                restaurant = []
                output = ""
                output += "<html><body>"

                if self.path.endswith("restEdit"):
                    # check if proper radio buttons are selected
                    if 'commOrCust' not in formInfo:
                        output += "<h1>You need to specify whether a"
                        output += "common or custom cuisine should be used</h1>"
                        output += "<h3>To try again, press your browser's"
                        output += "'back' button</h3>"
                        self.wfile.write(output)
                        print output
                        return
                    elif  ('commOrCust' in formInfo and
                           formInfo['commOrCust'][0] == 'common' and
                           'cuisine' not in formInfo):
                        output += "<h1>You chose 'use common cuisine', so you"
                        output += " need to select a particular common cuisine"
                        output += "<h3>To try again, press your browser's"
                        output += " 'back' button</h3>"
                        self.wfile.write(output)
                        print output
                        return
                    formInfo['form'] = 'restEdit'
                    localPath = re.search('/[0-9]+restEdit',\
                                          str(self.path)).group(0)
                    rest_id = re.search('[0-9]+',localPath).group(0)
                    restaurant = RestaurantManager.getRestaurant(int(rest_id))
                elif self.path.endswith("restDelete"):
                    formInfo['form'] = 'restDelete'
                    localPath = re.search('/[0-9]+restDelete',\
                                          str(self.path)).group(0)
                    rest_id = re.search('[0-9]+',localPath).group(0)
                    restaurant = RestaurantManager.getRestaurant(int(rest_id))
                elif self.path.endswith("restAdd"):
                    formInfo['form'] = 'restAdd'

                # use bleach on user provided text to defend SQL injection
                name = bleach.clean(formInfo['name'][0])
                cuisine = ""

                print formInfo
                
                if formInfo['commOrCust'][0] == 'custom':
                    cuisine = bleach.clean(formInfo['custCuisine'][0])
                else:
                    cuisine = formInfo['cuisine'][0]

                session = RestaurantManager.getRestaurantDBSession()

                message = ""
                
                if formInfo['form'] == 'restAdd':
                    if (len(nam) > 0 and len(cuisine) > 0):
                        newRestaurant = Restaurant(name=name,foodType=cuisine)
                        session.add(newRestaurant)
                        message += "Added %s " % name
                        message += "with cuisine type %s" % cuisine
                        message += " to the database"
                    else:
                        message += "Nothing added because name or cuisine empty"
                elif formInfo['form'] == 'restEdit':
                    message += "Made these changes to restaurant %s: " % rest_id
                    if (name == restaurant.name and
                        cuisine == restaurant.foodType):
                        message += "<br>None because name and cuisine were not "
                        message += "different"
                    elif (len(name) == 0 and len(cuisine) == 0):
                        print "empty"
                        message += "<br>None because name and cuisine fields "
                        message += "were empty"
                    else:
                        if name != restaurant.name:
                            print "new name"
                            session.query(Restaurant).\
                            filter(Restaurant.id==rest_id).\
                            update({'name':name})
                            message += "<br>Name from %s " % restaurant.name
                            message += "to %s" % name
                            print "done new name"
                        if cuisine != restaurant.foodType:
                            session.query(Restaurant).\
                            filter(Restaurant.id==rest_id).\
                            update({'foodType':cuisine})
                            message += "<br>Cuisine from %s " % restaurant.foodType
                            message += "to %s" % cuisine
                elif formInfo['form'] == 'restDelete':
                    session.query(Restaurant).\
                    filter(Restaurant.id==rest_id).\
                    delete()
                    message += "Deleted %s " % name
                    message += "(id %s )" % rest_id
                    message += " from the database"

                session.commit()
                session.close()

                output += "<h1>"+message+"</h1>"
                output += "<h3>To continue, navigate to another page</h3>"
                output += "</body><html>"
                
                self.wfile.write(output)
                print output
        except:
            pass

# instantiate server and specify port
def main():
    try:
        port = 8080
        server = HTTPServer(('',port),webserverHandler)
        print "Web server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print "^C entered, stopping web server..."
        server.socket.close()

# interpreter will run main method
if __name__ == '__main__':
    main()
