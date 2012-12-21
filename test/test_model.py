import os

from sqlalchemy import orm

from camelot.test import ModelThreadTestCase

class ModelCase( ModelThreadTestCase ):
    """Test the build in camelot model"""
  
    def setUp(self):
        super( ModelCase, self ).setUp()
        from camelot.model.party import Person
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( Person )
        
    def test_batch_job( self ):
        from camelot.model.batch_job import BatchJob, BatchJobType
        batch_job_type = BatchJobType.get_or_create( 'Synchronize' )
        with BatchJob.create( batch_job_type ) as batch_job:
            batch_job
    
    def test_current_authentication( self ):
        from camelot.model.authentication import get_current_authentication
        authentication = get_current_authentication()
        # current authentication cache should survive 
        # a session expire + expunge
        orm.object_session( authentication ).expire_all()
        orm.object_session( authentication ).expunge_all()
        authentication = get_current_authentication()
        self.assertTrue( authentication.username )
        
    def test_person_contact_mechanism( self ):
        from camelot.model.party import Person
        person = Person( first_name = u'Robin',
                         last_name = u'The brave' )
        self.assertEqual( person.contact_mechanisms_email, None )
        mechanism = ('email', 'robin@test.org')
        person.contact_mechanisms_email = mechanism
        self.person_admin.flush( person )
        self.assertEqual( person.contact_mechanisms_email, mechanism )
        self.person_admin.delete( person )
        person = Person( first_name = u'Robin',
                         last_name = u'The brave' )
        self.person_admin.flush( person )
        self.assertEqual( person.contact_mechanisms_email[1], u'' )
      
    def test_fixture_version( self ):
        from camelot.model.party import Person
        from camelot.model.fixture import FixtureVersion
        FixtureVersion.set_current_version( 'demo_data', 0 )
        self.assertEqual( FixtureVersion.get_current_version( 'demo_data' ),
                          0 )
        example_file = os.path.join( os.path.dirname(__file__), 
                                     '..', 
                                     'camelot_example',
                                     'import_example.csv' )
        person_count_before_import = Person.query.count()
        # begin load csv if fixture version
        import csv
        if FixtureVersion.get_current_version( 'demo_data' ) == 0:
            reader = csv.reader( open( example_file ) )
            for line in reader:
                Person( first_name = line[0], last_name = line[1] )
            FixtureVersion.set_current_version( 'demo_data', 1 )
            Person.query.session.flush()
        # end load csv if fixture version
        self.assertTrue( Person.query.count() > person_count_before_import )
        self.assertEqual( FixtureVersion.get_current_version( 'demo_data' ),
                          1 )
