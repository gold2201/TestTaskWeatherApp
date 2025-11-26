import logging

class ExtraFieldsFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'ip'):
            record.ip = 'unknown'
        if not hasattr(record, 'user'):
            record.user = 'anonymous'
        if not hasattr(record, 'event'):
            record.event = 'unknown'
        if not hasattr(record, 'city'):
            record.city = 'unknown'
        if not hasattr(record, 'units'):
            record.units = 'unknown'
        if not hasattr(record, 'served_from_cache'):
            record.served_from_cache = 'unknown'
        if not hasattr(record, 'latency'):
            record.latency = 'unknown'
        if not hasattr(record, 'error'):
            record.error = 'unknown'
        return True