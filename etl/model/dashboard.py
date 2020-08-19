import tg
from sqlalchemy.orm import mapper, relation, relationship
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, Boolean

from etl.model import DeclarativeBase
from ..lib.widgets import CodeTextArea, SmartWidgetTypes
from ..lib.helpers import is_number, is_boolean, is_datetime
import logging


log = logging.getLogger(__name__)


class DashboardExtractionAssociation(DeclarativeBase):
    __tablename__ = 'dashboard_extraction_associations'

    uid = Column(Integer, primary_key=True)
    dashboard_id = Column(Integer, ForeignKey('dashboards.uid'))
    extraction_id = Column(Integer, ForeignKey('extractions.uid'))
    dashboard = relationship('Dashboard')
    extraction = relationship('Extraction')
    index = Column(Integer)  # for sorting extractions in dashboard
    visualization = Column(Unicode(64), nullable=False)  # visualization type
    graph_axis = Column(Unicode(64), nullable=True)  # fields to visualize
    columns = Column(Integer, nullable=False)  # size of column for dashboard grid


class Dashboard(DeclarativeBase):
    __tablename__ = 'dashboards'

    uid = Column(Integer, primary_key=True)
    name = Column(Unicode(99), nullable=False)

    extractions = relationship('DashboardExtractionAssociation')
