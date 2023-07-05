from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import engine

# engine_str = DATABASE.get('engine').lower() + '://'
# engine_str += DATABASE.get('user') + ':'
# engine_str += DATABASE.get('password') + '@'
# engine_str += DATABASE.get('host') + ':'
# engine_str += DATABASE.get('port') + '/'
# engine_str += DATABASE.get('name')

# engine = sqlalchemy.create_engine(engine_str)
jobstore = {
    'default': SQLAlchemyJobStore(engine=engine)
}
scheduler = AsyncIOScheduler(jobstores=jobstore)
scheduler.start()
