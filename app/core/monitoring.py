from app.core.logging import setup_logger

logger = setup_logger(__name__)

class MetricsMonitor:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0

    def record_request(self):
        self.request_count += 1

    def record_error(self):
        self.error_count += 1
        self._check_alerts()

    def _check_alerts(self):
        # Trigger an alert every 3rd error for demonstration
        if self.error_count > 0 and self.error_count % 3 == 0:
            logger.critical(
                f"ALERT_ERROR_SPIKE: Detected high failure rate! "
                f"Total Errors: {self.error_count} | Total Requests: {self.request_count}"
            )

monitor = MetricsMonitor()