"""
celery_worker.py
----------------
Entry point for the Celery worker and beat scheduler.

The Celery app is created here and configured to use Flask's app context,
so tasks can access the database (db.session) and app.config just like
a normal Flask request would.

Started with:
  celery -A celery_worker.celery worker    (processes tasks)
  celery -A celery_worker.celery beat      (schedules periodic tasks)
"""

from celery import Celery
from celery.schedules import crontab
from app import create_app

flask_app = create_app()


def make_celery(app):
    """
    Create a Celery instance that runs inside the Flask app context.

    How it works:
    - We subclass Celery's Task class.
    - Every time a task runs, it pushes a Flask app context first.
    - This means db.session, app.config, and current_app all work
      inside task functions exactly like they do in route handlers.
    """
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(flask_app)

# ── Periodic task schedule ────────────────────────────────────────────────────
# Celery Beat reads this and queues tasks on the defined schedule.
# crontab(minute=0) means "at minute 0 of every hour" = hourly.
celery.conf.beat_schedule = {
    "refresh-all-products-hourly": {
        "task": "app.tasks.scrape_tasks.refresh_all_products",
        "schedule": crontab(minute=0),
    },
}

# TODO (stretch): Add a more frequent schedule for high-priority watchlist items
# TODO (stretch): Add a daily task to clean up old scrape_jobs logs
