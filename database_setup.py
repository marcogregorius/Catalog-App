from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    """
    Create a User table.
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    salt = Column(String(250))
    hashed_password = Column(String)


class Category(Base):
    """
    Create a Category table.
    """
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
        }


class Item(Base):
    """
    Create an Item table.
    """
    __tablename__ = 'item'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    description = Column(String(250))
    added_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'category_id': self.category_id,
            'description': self.description,
            'id': self.id,
            'name': self.name,
        }


engine = create_engine('sqlite:///catalognew.db')


Base.metadata.create_all(engine)
