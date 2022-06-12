import logging
from datetime import datetime

from sqlalchemy.orm import relationship
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class SatisfactionRating(Base):
    __tablename__ = 'satisfaction_ratings'


    id                      = Column(BigInteger(),primary_key=True)
    url                     = Column(String(255), nullable=False)
    assignee_id             = Column(BigInteger())
    group_id                = Column(BigInteger())
    requester_id            = Column(BigInteger())
    ticket_id               = Column(BigInteger())
    score                   = Column(String(255))
    created_at              = Column(DateTime())
    updated_at              = Column(DateTime())
    comment                 = Column(String(255))


    def __init__(self, **kwargs):
        
        self.id             = kwargs['id']
        self.url            = kwargs['url']
        self.assignee_id    = kwargs['assignee_id']
        self.group_id       = kwargs['group_id']
        self.requester_id   = kwargs['requester_id']
        self.ticket_id      = kwargs['ticket_id']
        self.score          = kwargs['score']
        self.created_at     = kwargs['created_at']
        self.updated_at     = kwargs['updated_at']
        self.comment        = kwargs['comment']


    def __str__(self):
        return self.url