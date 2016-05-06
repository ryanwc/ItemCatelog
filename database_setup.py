import sys

# import functionality from sqlalchemy
# these let you do SQL stuff in Python
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


# create an object that holds the database's data
Base = declarative_base()


# define tables for the database in Python classes

class Cuisine(Base):
        __tablename__ = 'cuisine'

        id = Column(Integer, primary_key=True)
        name = Column(String(80), nullable=False, unique=True)

        
class Restaurant(Base):
	__tablename__ = 'restaurant'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	cuisine_id = Column(Integer), ForeignKey(cuisine.id))
	cuisine = relationship(Cuisine)

class BaseMenuItem(Base):
	__tablename__ = 'base_menu_item'

	name = Column(String(80), nullable=False)
	id = Column(Integer, primary_key=True)
	description = Column(String(250))
	price = Column(String(8))
	course = Column(String(250))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	cuisine_id = Column(Integer, ForeignKey('cuisine.id'))
	restaurant = relationship(Restaurant)
	cuisine_id = relationship(Cuisine)

	@property
	def serialize(self):
                #Returns object data in easily serializeable format
                return {
                        'name': self.name,
                        'description': self.description,
                        'id': self.id,
                        'price': self.price,
                        'course': self.course,
                }

class RestaurantMenuItem(Base):
	__tablename__ = 'restaurant_menu_item'

	name = Column(String(80), nullable=False, unique=True)
	id = Column(Integer, primary_key=True)
	description = Column(String(250))
	price = Column(String(8))
	course = Column(String(250))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	baseMenuItem_id = Column(Integer, ForeignKey('base_menu_item.id'))
	restaurant = relationship(Restaurant)
	baseMenuItem = relationship(BaseMenuItem)
	

# connect to database engine
engine = create_engine('sqlite:///restaurantmenu.db')

# creates the database as new tables with the given engine/name
Base.metadata.create_all(engine)
