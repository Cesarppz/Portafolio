import logging
import traceback
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class Call(Base):
    __tablename__ = 'calls'

    id                              = Column(BigInteger(), primary_key=True)
    created_at                      = Column(DateTime(), nullable=False)
    updated_at                      = Column(DateTime(), nullable=False)
    agent_id                        = Column(BigInteger())
    call_charge                     = Column(Float())
    consultation_time               = Column(Integer())
    completion_status               = Column(String(50))
    customer_id                     = Column(BigInteger())
    customer_requested_voicemail    = Column(Boolean())
    direction                       = Column(String(255))
    duration                        = Column(BigInteger())
    exceeded_queue_wait_time        = Column(Boolean())
    hold_time                       = Column(BigInteger())
    minutes_billed                  = Column(BigInteger())
    outside_business_hours          = Column(Boolean())
    phone_number_id                 = Column(BigInteger())
    phone_number                    = Column(String(50))
    ticket_id                       = Column(BigInteger())
    time_to_answer                  = Column(BigInteger())
    voicemail                       = Column(Boolean())
    wait_time                       = Column(BigInteger())
    wrap_up_time                    = Column(BigInteger())
    ivr_time_spent                  = Column(BigInteger())
    ivr_hops                        = Column(BigInteger)
    ivr_destination_group_name      = Column(String(255))
    talk_time                       = Column(BigInteger())
    ivr_routed_to                   = Column(String(255))
    callback                        = Column(Boolean())
    callback_source                 = Column(String(50))
    default_group                   = Column(Boolean())
    ivr_action                      = Column(String(50))
    overflowed                      = Column(Boolean())
    overflowed_to                   = Column(String(25))
    recording_control_interactions  = Column(Integer())
    recording_time                  = Column(BigInteger())
    not_recording_time              = Column(BigInteger())
    call_recording_consent          = Column(String(25))
    call_recording_consent_action   = Column(String(25))
    call_recording_consent_keypress = Column(String(25))
    call_group_id                   = Column(BigInteger())
    call_channel                    = Column(String(105))
    quality_issues                  = Column(String(255))
    line                            = Column(String(50))
    line_id                         = Column(BigInteger())



    def __init__(self,**kwargs):
        try:
            self.id                                 = kwargs['id']
            self.created_at                         = kwargs['created_at']
            self.updated_at                         = kwargs['updated_at']
            self.agent_id                           = kwargs['agent_id']
            self.call_charge                        = kwargs['call_charge']
            self.consultation_time                  = kwargs['consultation_time']
            self.completion_status                  = kwargs['completion_status']
            self.customer_id                        = kwargs['customer_id']
            self.customer_requested_voicemail       = kwargs['customer_requested_voicemail']
            self.direction                          = kwargs['direction']
            self.duration                           = kwargs['duration']
            self.exceeded_queue_wait_time           = kwargs['exceeded_queue_wait_time']
            self.hold_time                          = kwargs['hold_time']
            self.minutes_billed                     = kwargs['minutes_billed']
            self.outside_business_hours             = kwargs['outside_business_hours']
            self.phone_number_id                    = kwargs['phone_number_id']
            self.phone_number                       = kwargs['phone_number']
            self.ticket_id                          = kwargs['ticket_id']
            self.time_to_answer                     = kwargs['time_to_answer']
            self.voicemail                          = kwargs['voicemail']
            self.wait_time                          = kwargs['wait_time']
            self.wrap_up_time                       = kwargs['wrap_up_time']
            self.ivr_time_spent                     = kwargs['ivr_time_spent']
            self.ivr_hops                           = kwargs['ivr_hops']
            self.ivr_destination_group_name         = kwargs['ivr_destination_group_name']
            self.talk_time                          = kwargs['talk_time']
            self.ivr_routed_to                      = kwargs['ivr_routed_to']
            self.callback                           = kwargs['callback']                                                                                                                                                                                                                                                        
            self.callback_source                    = kwargs['callback_source'] 
            self.default_group                      = kwargs['default_group']
            self.ivr_action                         = kwargs['ivr_action']
            self.overflowed                         = kwargs['overflowed']
            self.overflowed_to                      = kwargs['overflowed_to']
            self.recording_control_interactions     = kwargs['recording_control_interactions']
            self.recording_time                     = kwargs['recording_time']
            self.not_recording_time                 = kwargs['not_recording_time']
            self.call_recording_consent             = kwargs['call_recording_consent']
            self.call_recording_consent_action      = kwargs['call_recording_consent_action']
            self.call_recording_consent_keypress     = kwargs['call_recording_consent_keypress']
            self.call_group_id                      = kwargs['call_group_id']
            self.call_channel                       = kwargs['call_channel']
            self.quality_issues                     = kwargs['quality_issues']
            self.line                               = kwargs['line']
            self.line_id                            = kwargs['line_id']

        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "Calls"')
            traceback.print_exc(ex)

    
    def __str__(self):
        return self.id
