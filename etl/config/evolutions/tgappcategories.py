# -*- coding: utf-8 -*-
import json

from tgext.evolve import Evolution
from etl.model import ExtractionStep, DBSession, Group, Permission
import transaction
import logging

log = logging.getLogger('molepaw')


class CategoriesPermissions(Evolution):
    evolution_id = 'CategoriesPermission'

    def evolve(self):
        log.info('TgappCategories migration running')
        m = DBSession.query(Group).filter(Group.group_name == "managers").first()
        a = DBSession.query(Group).filter(Group.group_name == "admin").first()
        p = DBSession.query(Permission).filter(Permission.permission_name == "tgappcategories").first()
        p.groups.append(m)
        p.groups.append(a)

        DBSession.flush()
        transaction.commit()
