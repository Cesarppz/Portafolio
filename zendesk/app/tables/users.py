import logging
from datetime import datetime

from sqlalchemy.orm import relationship
from base import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, BigInteger, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Base')


class User(Base):
    __tablename__ = 'users'

    id                      = Column(BigInteger(), primary_key=True)
    url                     = Column(String(255), nullable=False)
    name                    = Column(String(255), nullable=False)
    email                   = Column(String(255))
    created_at              = Column(DateTime())
    updated_at              = Column(DateTime())
    time_zone               = Column(String(255))
    iana_time_zone          = Column(String(255))
    phone                   = String(String(255))
    shared_phone_number     = Column(String(255))
    photo                   = Column(JSONB)
    photo_url               = Column(String(255))
    locale_id               = Column(Integer())
    locale                  = Column(String(255))
    organization_id         = Column(Float())
    role                    = Column(String(255))
    verified                = Column(Boolean())
    external_id             = Column(BigInteger())
    tags                    = Column(Text())
    alias                   = Column(String(255))
    active                  = Column(Boolean())
    shared                  = Column(Boolean())
    shared_agent            = Column(Boolean())
    last_login_at           = Column(DateTime())
    two_factor_auth_enabled = Column(Boolean())
    signature               = Column(String(255))
    details                 = Column(String(255))
    notes                   = Column(String(255))
    role_type               = Column(Float())
    custom_role_id          = Column(Float())
    moderator               = Column(Boolean())
    ticket_restriction      = Column(String(255))
    only_private_comments   = Column(Boolean())
    restricted_agent        = Column(Boolean())
    suspended               = Column(Boolean())
    default_group_id        = Column(Float())
    report_csv              = Column(Boolean())
    user_fields_membership_level = Column(String(255))
    user_fields_membership_expires = Column(String(255))
    permanently_deleted     = Column(String(255))





    def __init__(self, **kwargs):
        try:
            self.id                     = kwargs['id']
            self.url                    = kwargs['url']
            self.name                   = kwargs['name']
            self.email                  = kwargs['email']
            self.created_at             = kwargs['created_at']
            self.updated_at              = kwargs['updated_at']
            self.time_zone              = kwargs['time_zone']
            self.iana_time_zone         = kwargs['iana_time_zone']
            self.phone                  = kwargs['phone']
            self.shared_phone_number    = kwargs['shared_phone_number']

            self.photo              = kwargs['photo']
            if self.photo:
                self.photo_url      = self.photo['url']
            else:
                self.photo_url      = None
            
            self.locale_id              = kwargs['locale_id']
            self.locale                 = kwargs['locale']
            self.organization_id        = kwargs['organization_id']
            self.role                   = kwargs['role']
            self.verified               = kwargs['verified']
            self.external_id            = kwargs['external_id'] 
            self.tags                   = '  /  '.join(kwargs['tags'])
            self.alias                  = kwargs['alias']
            self.active                 = kwargs['active']
            self.shared                 = kwargs['shared']
            self.shared_agent           = kwargs['shared_agent']
            self.last_login_at          = kwargs['last_login_at']
            self.two_factor_auth_enabled= kwargs['two_factor_auth_enabled']
            self.signature              = kwargs['signature']
            self.details                = kwargs['details']
            self.notes                  = kwargs['notes']
            self.role_type              = kwargs['role_type']
            self.custom_role_id         = kwargs['custom_role_id']
            self.moderator              = kwargs['moderator']
            self.ticket_restriction     = kwargs['ticket_restriction']
            self.only_private_comments  = kwargs['only_private_comments']
            self.restricted_agent       = kwargs['restricted_agent']
            self.suspended              = kwargs['suspended']
            self.default_group_id       = kwargs['default_group_id']
            self.report_csv             = kwargs['report_csv']

            try:
                self.user_fields_membership_level      = kwargs['user_fields']['membership_level']
            except KeyError:
                self.user_fields_membership_level      = None
            try:
                self.user_fields_membership_expires    = kwargs['user_fields']['membership_expires']
            except KeyError:
                self.user_fields_membership_expires    = None
            try:
                self.permanently_deleted                = kwargs['permanently_deleted']
            except KeyError:
                self.permanently_deleted                = None

        except Exception as ex:
            logger.error('Error generado al instanciar los datos en la tabla "users"', ex)

    def __str__(self):
        return self.url