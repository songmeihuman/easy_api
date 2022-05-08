from celery import Celery, signals
from click import Option

from easy_api import configs

app = Celery('tasks')
app.user_options['preload'].add(Option(('-C', '--config'),
                                       default='config.yaml',
                                       help='special easy_api config file'))


def update_celery_conf():
    app.conf.update(
        broker_url=configs.celery.broker,
        result_backend=configs.celery.backend,
        task_serializer=configs.celery.serializer,
        accept_content=[configs.celery.serializer],
        result_serializer=configs.celery.serializer,
        timezone=configs.celery.timezone,
        enable_utc=True,
        result_expires=60,
        task_soft_time_limit=10 * 60,
        task_time_limit=11 * 60
    )


@signals.user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    # there is start celery worker
    # update celery config after load project config
    configs.install(options['config'])
    install()
    app.autodiscover_tasks(configs.server.apps)


def install():
    # there is start easy_api server with celery
    update_celery_conf()
