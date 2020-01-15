# -*- coding: utf-8 -*-
"""Setup the etl application"""
from __future__ import print_function, unicode_literals
import transaction
from etl import model


def bootstrap(command, conf, vars):
    """Place any commands to setup etl here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        a = model.User()
        a.user_name = 'admin'
        a.display_name = 'Example Admin'
        a.email_address = 'admin@somedomain.com'
        a.password = 'adminpass'
        model.DBSession.add(a)

        g = model.Group()
        g.group_name = 'admin'
        g.display_name = 'Admins Group'
        g.users.append(a)
        model.DBSession.add(a)

        u = model.User()
        u.user_name = 'manager'
        u.display_name = 'Example manager'
        u.email_address = 'manager@somedomain.com'
        u.password = 'managepass'
        model.DBSession.add(u)

        g = model.Group()
        g.group_name = 'managers'
        g.display_name = 'Managers Group'
        g.users.append(u)
        g.users.append(a)
        model.DBSession.add(g)

        u1 = model.User()
        u1.user_name = 'viewer'
        u1.display_name = 'Example editor'
        u1.email_address = 'editor@somedomain.com'
        u1.password = 'viewpass'
        model.DBSession.add(u1)
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:  # pragma: no cover
        print('Warning, there was a problem adding your auth data, '
              'it may have already been added:')
        import traceback
        print(traceback.format_exc())
        transaction.abort()
        print('Continuing with bootstrapping...')

    # <websetup.bootstrap.after.auth>
