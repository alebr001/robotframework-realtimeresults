# # sinks/memory_sqlite.py
# import sqlite3
# from ..base import EventSink
# from shared.helpers.sql_definitions import (
#     CREATE_EVENTS_TABLE,
#     CREATE_RF_LOG_MESSAGE_TABLE,
#     INSERT_EVENT,
#     INSERT_RF_LOG_MESSAGE,
#     INSERT_APP_LOG,
#     INSERT_METRIC
# )

# class MemorySqliteSink(EventSink):
#     def __init__(self):
#         super().__init__()
#         self.conn = sqlite3.connect(":memory:")
#         self._initialize_schema()
#         self._dispatch_map = {
#             "start_test": self._insert_event,
#             "end_test": self._insert_event,
#             "start_suite": self._insert_event,
#             "end_suite": self._insert_event,
#             "log_message": self._insert_rf_log,
#             "app_log": self._insert_app_log,
#             "metric": self._insert_metric
#         }

#     def _initialize_schema(self):
#         try:
#             cursor = self.conn.cursor()
#             cursor.execute(CREATE_EVENTS_TABLE)
#             cursor.execute(CREATE_RF_LOG_MESSAGE_TABLE)
#             self.conn.commit()
#         except Exception as e:
#             self.logger.warning("[MEMORY_SQLITE] Failed to initialize in-memory schema: %s", e)
#             raise

#     def get_connection(self):
#         """
#         Expose connection for user in SqliteEventReader.
#         """
#         return self.conn

#     def _handle_event(self, data):
#         event_type = data.get("event_type")
#         handler = self._dispatch_map.get(event_type)

#         if handler:
#             try:
#                 handler(data)
#             except Exception as e:
#                 self.logger.warning("[MEMORY_SQLITE] Failed to handle '%s' event: %s", event_type, e)
#         else:
#             self.logger.debug("[MEMORY_SQLITE] Ignored unknown event type: %s", event_type)

#     def async_handle_event(self, data):
#         raise NotImplementedError("This function is not implemented.")

#     def _insert_event(self, data):
#         tags = data.get("tags", [])
#         if not isinstance(tags, list):
#             tags = [str(tags)]
#         tag_string = ",".join(str(tag) for tag in tags)

#         self.conn.execute(INSERT_EVENT, (
#             data.get("testid"),
#             data.get("timestamp"),
#             data.get("event_type"),
#             str(data.get("name")),
#             str(data.get("suite")),
#             data.get("status"),
#             data.get("message"),
#             data.get("elapsed"),
#             tag_string
#         ))
#         self.conn.commit()

#     def _insert_rf_log(self, data):
#         self.conn.execute(INSERT_RF_LOG_MESSAGE, (
#             data.get("testid"),
#             data.get("timestamp"),
#             data.get("message"),
#             data.get("level"),
#             int(data.get("html", False))
#         ))
#         self.conn.commit()

#     def _insert_app_log(self, data):
#         self.conn.execute(INSERT_APP_LOG, (
#             data.get("timestamp"),
#             data.get("message"),
#             data.get("source")
#         ))
#         self.conn.commit()

#     def _insert_metric(self, data):
#         self.conn.execute(INSERT_METRIC, (
#             data.get("timestamp"),
#             data.get("metric_name"),
#             data.get("value"),
#             data.get("unit"),
#             data.get("source")
#         ))
#         self.conn.commit()