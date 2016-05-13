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

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(30), nullable=False)
	email = Column(String(30), unique=True, nullable=False)
	picture = Column(String(200))

	@property
	def serialize(self):
                return {
                        'name': self.name,
                        'id': self.id,
                        'email': self.email,
                        'picture': self.picture,
                }

class Cuisine(Base):
	__tablename__ = 'cuisine'

	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False, unique=True)

	@property
	def serialize(self):
                return {
                        'name': self.name,
                        'id': self.id,
                }

        
class Restaurant(Base):
	__tablename__ = 'restaurant'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	cuisine_id = Column(Integer, ForeignKey('cuisine.id'))
	user_id = Column(Integer, ForeignKey('user.id'))
	cuisine = relationship(Cuisine)
	user = relationship(User)

	@property
	def serialize(self):
                return {
                        'name': self.name,
                        'id': self.id,
                        'cuisine_id': self.cuisine_id,
                        'user_id': self.user_id,
                }

class BaseMenuItem(Base):
	__tablename__ = 'base_menu_item'

	name = Column(String(80), nullable=False, unique=True)
	id = Column(Integer, primary_key=True)
	description = Column(String(250))
	price = Column(String(8))
	course = Column(String(250))
	cuisine_id = Column(Integer, ForeignKey('cuisine.id'))
	cuisine = relationship(Cuisine)

	@property
	def serialize(self):
                return {
                        'name': self.name,
                        'description': self.description,
                        'id': self.id,
                        'price': self.price,
                        'course': self.course,
                        'cuisine_id':self.cuisine_id,
                }

class RestaurantMenuItem(Base):
	__tablename__ = 'restaurant_menu_item'

	name = Column(String(80), nullable=False)
	id = Column(Integer, primary_key=True)
	description = Column(String(250))
	price = Column(String(8))
	course = Column(String(250))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	baseMenuItem_id = Column(Integer, ForeignKey('base_menu_item.id'))
	restaurant = relationship(Restaurant)
	baseMenuItem = relationship(BaseMenuItem)

	@property
	def serialize(self):
                return {
                        'name': self.name,
                        'description': self.description,
                        'id': self.id,
                        'price': self.price,
                        'course': self.course,
                        'restaurant_id':self.restaurant_id,
                        'baseMenuItem_id':self.baseMenuItem_id,
                }


# connect to database engine
engine = create_engine('sqlite:///restaurants.db')

# creates the database as new tables with the given engine/name
Base.metadata.create_all(engine)
