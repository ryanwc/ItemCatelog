from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# import common gateway interface
import cgi

import RestaurantManager
from database_setup import Base, Restaurant, MenuItem

import bleach

# handler -- specify what to do based on type of request
class webserverHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
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
                    output += "<a href=/edit>Edit</a>"
                    output += " | "
                    output += "<a href=/delete>Delete</a>"
                    output += "</p>"
                
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return
            if self.path.endswith("/newrestaurant"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurants = RestaurantManager.getRestaurants()
                popCuisines = RestaurantManager.getPopularCuisines()

                output = ""
                output += "<html><body>"
                output += "<h1>Enter a New Restaurant into the Database</h1>"
                output += "<form method='POST' enctype='multipart/form-data'>"
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

                # use bleach on user provided text to defend SQL injection
                name = bleach.clean(formInfo['name'][0])
                cuisine = ""
                
                if formInfo['commOrCust'][0] == 'custom':
                    cuisine = bleach.clean(formInfo['custCuisine'][0])
                else:
                    cuisine = formInfo['cuisine'][0]

                newRestaurant = Restaurant(name=name,foodType=cuisine)
                session = RestaurantManager.getRestaurantDBSession()
                session.add(newRestaurant)
                session.commit()
                session.close()
                
                message = ""
                message += "Added %s " % name
                message += "with cuisine type %s" % cuisine
                message += " to the database"

                output = ""
                output += "<html><body>"
                output += "<h1>"+message+"</h1>"
                output += "<h3>To continue, refresh the page "
                output += "or navigate to another page"
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
