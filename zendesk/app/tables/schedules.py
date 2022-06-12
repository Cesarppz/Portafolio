import logging
from datetime import datetime

from sqlalchemy.orm import relationship
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class Schedule(Base):
    __tablename__ = 'schedules'

    id                      = Column(BigInteger(),primary_key=True)
    name                    = Column(String(255))
    time_zone               = Column(String(255))
    created_at              = Column(DateTime())
    updated_at              = Column(DateTime())
    intervals               = relationship('Interval',backref='schedule')


    def __init__(self,**kwargs):
        self.id         = kwargs['id']
        self.name       = kwargs['time_zone']
        self.created_at = kwargs['created_at']
        self.updated_at = kwargs['updated_at']

    
    def __str__(self):
        return self.id


class Interval(Base):
    __tablename__ = 'intervals'

    id          = Column(Integer(), primary_key=True)
    schedule_id = Column(ForeignKey('schedules.id'))
    start_time  = Column(Integer())
    end_time    = Column(Integer())
    created_at  = Column(DateTime())
    updated_at  = Column(DateTime())


    def __init__(self, **kwargs):
        
        self.id          = None
        self.schedule_id = kwargs['id']
        self.start_time  = kwargs['start_time']
        self.end_time    = kwargs['end_time']
        self.created_at  = kwargs['created_at']
        self.updated_at  = kwargs['updated_at']

    
    def __str__(self):
        return self.id

    