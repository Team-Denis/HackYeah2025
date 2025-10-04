

from db import Database, UserRepository, ReportRepository, IncidentRepository



if __name__ == "__main__":

    db: Database = Database("app.db")
    db.fill_types()