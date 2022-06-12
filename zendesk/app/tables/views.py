import logging
from datetime import datetime

from sqlalchemy.orm import relationship
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class View(Base):
    __tablename__ = 'views'

    id                      = Column(BigInteger(), primary_key=True)
    url                     = Column(String(255))
    title                   = Column(String(255))
    active                  = Column(Boolean())
    updated_at              = Column(DateTime())
    created_at              = Column(DateTime())
    position                = Column(Integer())
    description             = Column(String(255))
    execution               = Column(JSONB)
    conditions              = Column(JSONB)
    restriction             = Column(JSONB)
    watchable               = Column(Boolean())


    def __init__(self, **kwargs):
        try:
            self.id         = kwargs['id']
            self.url        = kwargs['url']
            self.title      = kwargs['title']
            self.active     = kwargs['active']
            self.updated_at = kwargs['updated_at']
            self.created_at = kwargs['created_at']
            self.position   = kwargs['position']
            self.description= kwargs['description']
            self.execution  = kwargs['execution']
            self.conditions = kwargs['conditions']
            self.restriction= kwargs['restriction']
            self.watchable  = kwargs['watchable']
            
        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "View"')
        

    
    def __str__(self):
        return self.url