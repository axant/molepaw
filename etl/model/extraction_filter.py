# -*- coding: utf-8 -*-
"""Extraction model module."""
import json

from sqlalchemy import Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, Unicode

from etl.model import DeclarativeBase, DBSession


class ExtractionFilter(DeclarativeBase):
    __tablename__ = 'extraction_filters'

    uid = Column(Integer, primary_key=True)
    name = Column(Unicode(99), nullable=False)
    extraction_id = Column(Integer, ForeignKey('extractions.uid'), index=True)
    extraction = relationship('Extraction', uselist=False)
    steps = relationship('ExtractionStep', cascade='all, delete-orphan', order_by="ExtractionStep.priority")
    default = Column(Boolean, default=False, nullable=False)

    def perform(self, df=None):
        if df is None:
            df = self.extraction.perform()
        for step in self.steps:
            df = step.apply(df)
        return df

    @classmethod
    def set_default(cls, e_filter):
        prev_default = DBSession.query(ExtractionFilter).filter(
            ExtractionFilter.extraction_id == e_filter.extraction.uid,
            ExtractionFilter.default == True).all()
        for p in prev_default:
            p.default = False
        e_filter.default = True

    @property
    def query(self):
        return json.loads(self.steps[0].options)['expression']

    def __json__(self):
        return dict(
            uid=self.uid,
            name=self.name,
            extraction_id=self.extraction_id,
            default=self.default,
            query=self.query,
            steps=self.steps
        )


__all__ = ['ExtractionFilter']
