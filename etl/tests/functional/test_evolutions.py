from etl import model
from etl.tests import TestController
from etl.config.evolutions.tgappcategories import CategoriesPermissions
from etl.config.evolutions.e01_options_dict import EvolveOptionsDict
from etl.config.evolutions.dashboard_creation import DashboardCreationEvolution

class TestEvolutionsController(TestController):
    """Tests for the methods in the posts controller."""
 
    def test_tgappcategories_evolution(self):
        p = model.DBSession.query(model.Permission).filter(
            model.Permission.permission_name == 'tgappcategories'
        ).all()
        assert len(p[0].groups) == 0, p
        # runnning migration to associate this permission to groups
        CategoriesPermissions().evolve()
        p = model.DBSession.query(model.Permission).filter(
            model.Permission.permission_name == 'tgappcategories'
        ).one()
        assert len(p.groups) != 0, p

    def test_dashboard_creation_evolution(self):
        d = model.DBSession.query(model.Dashboard).all()
        assert len(d) == 0
        DashboardCreationEvolution().evolve()
        d = model.DBSession.query(model.Dashboard).all()
        assert len(d) == 1
        assert d[0].name == 'main dashboard'

    # def test_evolve_options_dict_evolution(self):
    # the effort required to test this could be used somewhere else
