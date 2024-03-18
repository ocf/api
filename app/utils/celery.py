"""Load Celery tasks for account submission.

This module is responsible for instantiating the Celery tasks used for account
creation using our special credentials. Other modules should import from here,
rather than from ocflib directly.
"""

import ssl

from celery import Celery

from ocflib.account.submission import get_tasks as real_get_tasks

from utils.config import get_settings

settings = get_settings()

celery_app = Celery(
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)
celery_app.conf.broker_use_ssl = {
    "ssl_ca_certs": "/etc/ssl/certs/ca-certificates.crt",
    "ssl_cert_reqs": ssl.CERT_REQUIRED,
}
celery_app.conf.redis_backend_use_ssl = {
    "ssl_ca_certs": "/etc/ssl/certs/ca-certificates.crt",
    "ssl_cert_reqs": ssl.CERT_REQUIRED,
}

# TODO: stop using pickle
celery_app.conf.task_serializer = "pickle"
celery_app.conf.result_serializer = "pickle"
celery_app.conf.accept_content = {"pickle"}

_tasks = real_get_tasks(celery_app)

create_account = _tasks.create_account
validate_then_create_account = _tasks.validate_then_create_account
get_pending_requests = _tasks.get_pending_requests
approve_request = _tasks.approve_request
reject_request = _tasks.reject_request
change_password = _tasks.change_password
