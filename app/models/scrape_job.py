"""
models/scrape_job.py
--------------------
An audit log of every scrape attempt — successful or failed.

Why log this separately from the Product?
The Product table tracks current state ("what is the price right now?").
The ScrapeJob table tracks operational history ("what happened when we tried
to scrape?"). Mixing them would clutter the Product model and make it harder
to query failed jobs independently.

This powers the /admin page where you can see:
- Which products are consistently failing
- What the error message was
- How long each scrape took

status values:
- 'pending'  — task queued but not started
- 'success'  — scrape completed and price recorded
- 'failed'   — scrape threw an exception (see error_message)
"""

from datetime import datetime, timezone
from app.extensions import db


class ScrapeJob(db.Model):
    __tablename__ = "scrape_jobs"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    status = db.Column(db.String(20), nullable=False, default="pending")
    error_message = db.Column(db.Text, nullable=True)
    attempted_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    # How many milliseconds the scrape HTTP request took
    # Useful for spotting slow or timing-out sites
    duration_ms = db.Column(db.Integer, nullable=True)

    # Relationship
    product = db.relationship("Product", back_populates="scrape_jobs")

    def __repr__(self) -> str:
        return f"<ScrapeJob product={self.product_id} status={self.status}>"
