from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ARRAY

Base = declarative_base()


class Requests(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    status = Column(String)
    website_text = Column(String)
    pictures = Column(ARRAY(String))

    def __repr__(self):
        return "<Requests(id='{}', url='{}', status={}, website_text={}, pictures={})>" \
            .format(self.id, self.url, self.status, self.website_text, self.pictures)
