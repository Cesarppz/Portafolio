import logging
from datetime import datetime
from xmlrpc.client import DateTime

from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime
from sqlalchemy.orm import relationship

from tables.ticket_metrics import Ticket_Metrics
from tables.users import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class Record(Base):
    __tablename__ = 'records'

    id          = Column(Integer(), primary_key=True)
    created_at  = Column(DateTime(), nullable=False, default=datetime.now().replace(second=0, microsecond=0))


    def __init__(self, id=None,created_at=None):
        
        self.id          = id
        self.created_at  = created_at

    def __str__(self):
        return self.created_at