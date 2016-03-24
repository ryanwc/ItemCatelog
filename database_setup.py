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
class Restaurant(Base):
	__tablename__ = 'restaurant'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	foodType = Column(String(250))

class MenuItem(Base):
	__tablename__ = 'menu_item'

	name = Column(String(80), nullable=False)
	id = Column(Integer, primary_key=True)
	description = Column(String(250))
	price = Column(String(8))
	course = Column(String(250))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	restaurant = relationship(Restaurant)


# connect to database engine
engine = create_engine('sqlite:///restaurantmenu.db')

# creates the database as new tables with the given engine/name
Base.metadata.create_all(engine)
