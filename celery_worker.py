import os

from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    celery = Celery(app.import_name)

    # Pull broker/backend from Flask config
    celery.conf.update(
        broker_url=app.config.get("broker_url", os.environ.get("REDIS_URL", "redis://redis:6379/0")),
        result_backend=app.config.get("result_backend", os.environ.get("REDIS_URL", "redis://redis:6379/0")),
        include=["app.tasks.scrape_tasks", "app.tasks.alert_tasks"],
        broker_connection_retry_on_startup=True,
        beat_schedule={
            "refresh-all-products-hourly": {
                "task": "app.tasks.scrape_tasks.refresh_all_products",
                "schedule": crontab(minute=0),
            },
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # This is the key line — registers @shared_task decorators
    celery.set_default()

    return celery


from app import create_app

flask_app = create_app()
celery = make_celery(flask_app)