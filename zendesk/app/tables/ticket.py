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


class Ticket(Base):
    __tablename__ = 'tickets'

    id                      = Column(BigInteger(), primary_key=True)
    url                     = Column(String(255))
    external_id             = Column(BigInteger(),  nullable=True)
    via_channel             = Column(String(255), nullable=False)
    via_source_from         = Column(String(255))
    via_source_to           = Column(String(255))
    via_source_rel          = Column(String(255))
    created_at              = Column(DateTime())
    updated_at               = Column(DateTime()) ######
    type                    = Column(String(255), nullable=True)
    subject                 = Column(String(255))
    raw_subject             = Column(String(255))
    description             = Column(Text())
    priority                = Column(String(255), nullable=True)
    status                  = Column(String(255))
    recipient               = Column(String(255), nullable=True)
    requester_id            = Column(BigInteger())
    submitter_id            = Column(BigInteger(), nullable=False)
    assignee_id             = Column(BigInteger(), nullable=True)
    organization_id         = Column(BigInteger(), nullable=True)
    group_id                = Column(BigInteger(), nullable=True)
    collaborator_ids        = Column(Text(), nullable=True)
    follower_ids            = Column(Text(), nullable=True)
    email_cc_ids            = Column(Text(),nullable=True)
    forum_topic_id          = Column(BigInteger(), nullable=True)
    problem_id              = Column(BigInteger(), nullable=True)
    has_incidents           = Column(Boolean(), nullable=False)
    is_public               = Column(Boolean(), nullable=False)
    due_at                  = Column(Text(), nullable=True)
    tags                    = Column(Text(), nullable=True)
    custom_fields           = relationship('Custom_field', backref="ticket")
    satisfaction_rating     = Column(String(255), nullable=True)
    sharing_agreement_ids   = Column(String(255), nullable=True)
    fields                  = relationship('Field', backref="ticket")
    followup_ids            = Column(String(255), nullable=True)
    ticket_form_id          = Column(BigInteger(), nullable=False)
    brand_id                = Column(BigInteger(), nullable=False)
    allow_channelback       = Column(Boolean, nullable=False)
    allow_attachments       = Column(Boolean, nullable=False)
    generated_timestamp     = Column(BigInteger())
    # ticket_metrics          = relationship('Ticket_Metrics',backref="ticket")


    def __init__(self, **kwargs):
        try:
            self.id                     = kwargs['id']
            self.url                    = kwargs['url']
            self.external_id            = kwargs['external_id']
            self.external_id            = kwargs['external_id']
            self.via_channel            = kwargs['via']['channel']
            
            try:
                self.via_source_from    = str(kwargs['via']['source']['from'])
            except KeyError as err:
                self.via_source_from   = None
            except TypeError :
                 self.via_source_from   = None

            try:
                self.via_source_to      = str(kwargs['via']['source']['to'])
            except KeyError as err:
                self.via_source_to      = None
            except TypeError :
                self.via_source_to      = None
                
            try:
                self.via_source_rel     = kwargs['via']['source']['rel']
            except KeyError as err:
                self.via_source_rel     = None
            except TypeError :
                self.via_source_rel     = None
                        
            self.created_at             = datetime.strptime(kwargs['created_at'],"%Y-%m-%dT%H:%M:%S%z")
            self.updated_at              = kwargs['updated_at']
            self.type                   = kwargs['type']
            self.subject                = kwargs['subject']
            self.raw_subject            = kwargs['raw_subject']
            self.description            = kwargs['description']
            self.priority               = kwargs['priority']
            self.status                 = kwargs['status']
            self.recipient              = kwargs['recipient']
            self.requester_id           = kwargs['requester_id']
            self.submitter_id           = kwargs['submitter_id']
            self.assignee_id            = kwargs['assignee_id']
            self.organization_id        = kwargs['organization_id']
            self.group_id               = kwargs['group_id']
            self.collaborator_ids       = '  /  '.join(str(kwargs['collaborator_ids']))  #Conateno los id para formar una string separando los ids por '  /  '
            self.follower_ids           = '  /  '.join(str(kwargs['follower_ids'])) 
            self.email_cc_ids           = '  /  '.join(str(kwargs['email_cc_ids']))
            self.forum_topic_id         = kwargs['forum_topic_id']
            self.problem_id             = kwargs['problem_id']
            self.has_incidents          = kwargs['has_incidents']
            self.is_public              = kwargs['is_public']
            self.due_at                 = kwargs['due_at']
            self.tags                   = '  /  '.join(str(kwargs['tags']))
            self.satisfaction_rating    = kwargs['satisfaction_rating']['score']
            self.sharing_agreement_ids  = '  /  '.join(str(kwargs['sharing_agreement_ids']))
            self.followup_ids           = '  /  '.join(str(kwargs['followup_ids']))
            self.ticket_form_id         = kwargs['ticket_form_id']
            self.brand_id               = kwargs['brand_id']
            self.allow_channelback      = kwargs['allow_channelback']
            self.allow_attachments      = kwargs['allow_attachments']
            self.generated_timestamp    = kwargs['generated_timestamp']
        
        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "tickets"', ex)


    def __str__(self):
        return self.url


class Custom_field(Base):
    __tablename__ = 'custom_fields'

    id          = Column(BigInteger(), primary_key=True)
    value       = Column(String(255))
    ticket_id   = Column(ForeignKey('tickets.id'))
    updated_at  = Column(DateTime())
    created_at  = Column(DateTime())

    def __init__(self, **kwargs):
        self.value      = kwargs['id']
        self.value      = kwargs['value']
        self.ticket_id  = kwargs['ticket_id']
        self.updated_at  = kwargs['updated_at']
        self.created_at = datetime.strptime(kwargs['created_at'],"%Y-%m-%dT%H:%M:%S%z")

    def __str__(self):
        return self.value


class Field(Base):
    __tablename__ = 'fields'

    id          = Column(BigInteger(), primary_key=True)
    value       = Column(String(255))
    ticket_id   = Column(ForeignKey('tickets.id'))
    updated_at  = Column(DateTime())
    created_at  = Column(DateTime())

    def __init__(self, **kwargs):
        self.value      = kwargs['id']
        self.value      = kwargs['value']
        self.ticket_id  = kwargs['ticket_id']
        self.updated_at = kwargs['updated_at']
        self.created_at = datetime.strptime(kwargs['created_at'],"%Y-%m-%dT%H:%M:%S%z")

    def __str__(self):
        return self.value
