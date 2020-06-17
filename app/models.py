import enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ARRAY, Enum, Column, Integer, String

Base = declarative_base()


class Status(enum.Enum):
    preparing = "in-progress"
    done = "done"


class Requests(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    url = Column(String(2083))
    status = Column(Enum(Status))
    website_text = Column(String)
    images = Column(ARRAY(String))

    def __repr__(self):
        return "<Requests(url='{}', status={}, website_text={}, images={})>" \
            .format(self.url, self.status, self.website_text, self.images)
