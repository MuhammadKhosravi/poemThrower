from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DBConnector:
    def __init__(self, host, user, password, database):
        self.engine = create_engine(

            f'mysql+mysqlconnector://{user}:{password}@{host}/{database}'
        )
        self.session = None

    def create_session(self):
        self.session = sessionmaker(bind=self.engine)()

