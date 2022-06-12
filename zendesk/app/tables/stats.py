import logging
from datetime import datetime

from sqlalchemy.orm import relationship
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class Stats(Base):
    __tablename__ = 'stats'

    # id                                         = Column(Integer(),)
    updated_at                                 = Column(DateTime(),  primary_key=True)
    average_call_duration                      = Column(Integer())
    average_callback_wait_time                 = Column(Integer())
    average_hold_time                          = Column(Integer())
    average_queue_wait_time                    = Column(Integer())
    average_time_to_answer                     = Column(Integer())
    average_wrap_up_time                       = Column(Integer())
    max_calls_waiting                          = Column(Integer())
    max_queue_wait_time                        = Column(Integer())
    total_call_duration                        = Column(Integer())
    total_callback_calls                       = Column(Integer())
    total_calls                                = Column(Integer())
    total_calls_abandoned_in_queue             = Column(Integer())
    total_calls_outside_business_hours         = Column(Integer())
    total_calls_with_exceeded_queue_wait_time  = Column(Integer())
    total_calls_with_requested_voicemail       = Column(Integer())
    total_embeddable_callback_calls            = Column(Integer())
    total_hold_time                            = Column(Integer())
    total_inbound_calls                        = Column(Integer())
    total_outbound_calls                       = Column(Integer())
    total_textback_requests                    = Column(Integer())
    total_voicemails                           = Column(Integer())
    total_wrap_up_time                         = Column(Integer())


    def __init__(self,  id=None, **kwargs):

        try:
            # self.id                                         = id
            self.updated_at                                 = datetime.now().replace(second=0, microsecond=0)
            self.average_call_duration                      = kwargs['average_call_duration']
            self.average_callback_wait_time                 = kwargs['average_callback_wait_time']
            self.average_hold_time                          = kwargs['average_hold_time']
            self.average_queue_wait_time                    = kwargs['average_queue_wait_time']
            self.average_time_to_answer                     = kwargs['average_time_to_answer']
            self.average_wrap_up_time                       = kwargs['average_wrap_up_time']
            self.max_calls_waiting                          = kwargs['max_calls_waiting']
            self.max_queue_wait_time                        = kwargs['max_queue_wait_time']
            self.total_call_duration                        = kwargs['total_call_duration']
            self.total_callback_calls                       = kwargs['total_callback_calls']
            self.total_calls                                = kwargs['total_calls']
            self.total_calls_abandoned_in_queue             = kwargs['total_calls_abandoned_in_queue']
            self.total_calls_outside_business_hours         = kwargs['total_calls_outside_business_hours']
            self.total_calls_with_exceeded_queue_wait_time  = kwargs['total_calls_with_exceeded_queue_wait_time']
            self.total_calls_with_requested_voicemail       = kwargs['total_calls_with_requested_voicemail']
            self.total_embeddable_callback_calls            = kwargs['total_embeddable_callback_calls']
            self.total_hold_time                            = kwargs['total_hold_time']
            self.total_inbound_calls                        = kwargs['total_inbound_calls']
            self.total_outbound_calls                       = kwargs['total_outbound_calls']
            self.total_textback_requests                    = kwargs['total_textback_requests']
            self.total_voicemails                           = kwargs['total_voicemails']
            self.total_wrap_up_time                         = kwargs['total_wrap_up_time']
            
        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "tickets"', ex)


    def __str__(self) -> str:
        return self.created_at
