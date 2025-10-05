from core import Routine
from db import Database, GeneralRepository, UserRepository

if __name__ == "__main__":

    db: Database = Database("app.db")
    db.fill_types()

    gr: GeneralRepository = GeneralRepository(db)
    ur: UserRepository = UserRepository(db)
    uid1: int = ur.add_user('Ant0in', 'antoine.berthion@ulb.be')
    uid2: int = ur.add_user('bob', 'bob@bob.bob')
    routine = Routine(db)
    routine.run()
