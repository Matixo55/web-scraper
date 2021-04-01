import enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ARRAY, Enum, Column, Integer, String

Base = declarative_base()

list_model = """
    <table style="width:100%">
    <tr>
    <th>ID</th>
    <th>URL</th>
    <th>Status</th>
    </tr>
    """

class Status(enum.Enum):
    preparing = "in-progress"
    done = "done"
    invalid = "invalid"

class Requests(Base):
    __tablename__ = "requests"
    id = Column("id", Integer, primary_key=True)
    url = Column("url", String(2083))
    status = Column("status", Enum(Status))
    website_text = Column("website_text", String)
    images = Column("images", ARRAY(String))

