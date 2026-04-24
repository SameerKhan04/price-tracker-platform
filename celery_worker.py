import os
from celery import Celery
from celery.schedules import crontab
from app import create_app

flask_app = create_app()


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(flask_app)

celery.conf.beat_schedule = {
    "refresh-all-products-hourly": {
        "task": "app.tasks.scrape_tasks.refresh_all_products",
        "schedule": crontab(minute=0),
    },
}

# TODO (stretch): Add a daily task to clean up old scrape_job logs
