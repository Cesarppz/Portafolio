import logging
from datetime import datetime

from base import Base
from sqlalchemy import Column, Date, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime

#from ticket import Ticket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class Ticket_Metrics(Base):
    __tablename__ = 'tickets_metrics'

    id                                           = Column(BigInteger(), primary_key=True)
    url                                          = Column(String(255))
    ticket_id                                    = Column(BigInteger())
    created_at                                   = Column(DateTime(), nullable=False)
    updated_at                                    = Column(DateTime(), nullable=False)
    group_stations                               = Column(BigInteger())
    assignee_stations                            = Column(BigInteger())
    reopens                                      = Column(BigInteger())
    replies                                      = Column(BigInteger())
    assignee_updated_at                          = Column(DateTime())
    requester_updated_at                         = Column(DateTime())
    status_updated_at                            = Column(DateTime())
    initially_assigned_at                        = Column(DateTime())
    assigned_at                                  = Column(DateTime())
    solved_at                                    = Column(DateTime())
    latest_comment_added_at                      = Column(DateTime())
    reply_time_in_minutes_calendar               = Column(Integer(), nullable=True)
    reply_time_in_minutes_business               = Column(Integer(), nullable=True)
    first_resolution_time_in_minutes_calendar    = Column(Integer(), nullable=True)
    first_resolution_time_in_minutes_business    = Column(Integer(), nullable=True)
    full_resolution_time_in_minutes_calendar     = Column(Integer(), nullable=True)
    full_resolution_time_in_minutes_business     = Column(Integer(), nullable=True)
    agent_wait_time_in_minutes_calendar          = Column(Integer(), nullable=True)
    agent_wait_time_in_minutes_business          = Column(Integer(), nullable=True)
    requester_wait_time_in_minutes_calendar      = Column(Integer(), nullable=True)
    requester_wait_time_in_minutes_business      = Column(Integer(), nullable=True)
    on_hold_time_in_minutes_calendar             = Column(Integer(), nullable=True)
    on_hold_time_in_minutes_business             = Column(Integer(), nullable=True)


    def __init__(self, **kwargs):
        try:
            self.id                                         = kwargs['id']
            self.url                                        = kwargs['url']
            self.ticket_id                                  = kwargs['ticket_id']
            self.created_at                                 = datetime.strptime(kwargs['created_at'],"%Y-%m-%dT%H:%M:%S%z")
            self.updated_at                                  = kwargs['updated_at']
            self.group_stations                             = kwargs['group_stations']
            self.assignee_stations                          = kwargs['assignee_stations']
            self.reopens                                    = kwargs['reopens']
            self.replies                                    = kwargs['replies']
            try:
                self.assignee_updated_at                    = datetime.strptime(kwargs['assignee_updated_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.assignee_updated_at                    = None

            try:
                self.requester_updated_at                   = datetime.strptime(kwargs['requester_updated_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.requester_updated_at                   = None
            
            try:
                self.status_updated_at                      = datetime.strptime(kwargs['status_updated_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.status_updated_at                      = None
            
            try:
                self.initially_assigned_at                  = datetime.strptime(kwargs['initially_assigned_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.initially_assigned_atq                 = None
            
            try:
                self.assigned_at                                = datetime.strptime(kwargs['assigned_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.assigned_at                            = None
            
            try:
                self.solved_at                              = datetime.strptime(kwargs['solved_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.solved_at                              = None
            
            try:
                self.latest_comment_added_at                = datetime.strptime(kwargs['latest_comment_added_at'],"%Y-%m-%dT%H:%M:%S%z")
            except TypeError:
                self.latest_comment_added_at                = None
            
            self.reply_time_in_minutes_calendar             = kwargs['reply_time_in_minutes']['calendar']
            self.reply_time_in_minutes_business             = kwargs['reply_time_in_minutes']['business']
            self.first_resolution_time_in_minutes_calendar  = kwargs['first_resolution_time_in_minutes']['calendar']
            self.first_resolution_time_in_minutes_business  = kwargs['first_resolution_time_in_minutes']['business']
            self.full_resolution_time_in_minutes_calendar   = kwargs['full_resolution_time_in_minutes']['calendar']
            self.full_resolution_time_in_minutes_business   = kwargs['full_resolution_time_in_minutes']['business']        
            self.agent_wait_time_in_minutes_calendar        = kwargs['agent_wait_time_in_minutes']['calendar']
            self.agent_wait_time_in_minutes_business        = kwargs['agent_wait_time_in_minutes']['business']
            self.requester_wait_time_in_minutes_calendar    = kwargs['requester_wait_time_in_minutes']['calendar']
            self.requester_wait_time_in_minutes_business    = kwargs['requester_wait_time_in_minutes']['business']
            self.on_hold_time_in_minutes_calendar           = kwargs['on_hold_time_in_minutes']['calendar']
            self.on_hold_time_in_minutes_business           = kwargs['on_hold_time_in_minutes']['business']
            
        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "tickets_metrics"')
        

    def __str__(self):
        return self.url