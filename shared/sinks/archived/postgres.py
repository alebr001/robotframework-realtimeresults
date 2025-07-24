# import psycopg2
# import json
# from pathlib import Path

# from shared.helpers.ensure_db_schema import ensure_schema
# from ..base import EventSink
# import shared.helpers.sql_definitions as sql_definitions


# class PostgresSink(EventSink):
#     def __init__(self, database_url=None):
#         super().__init__()
#         from shared.helpers.config_loader import load_config
#         config = load_config()
#         self.database_url = database_url or config.get("db_url")
#         self.dispatch_map = {
#             "start_test": self._insert_rf_event,
#             "end_test": self._insert_rf_event,
#             "start_suite": self._insert_rf_event,
#             "start_keyword": self._insert_rf_event,
#             "end_keyword": self._insert_rf_event,
#             "end_suite": self._insert_rf_event,
#             "log_message": self._insert_rf_log,
#         }
#         self._initialize_database()

#     def _initialize_database(self):
#         self.logger.info("Ensuring PostgreSQL schema exists at: %s", self.database_url)
#         try:
#             ensure_schema(self.database_url)
#         except Exception as e:
#             self.logger.warning("[POSTGRES_SYNC] DB init failed: %s", e)
#             raise

#     # In synchronous sinks, the database connection is managed centrally in the dispatcher.
#     # Handlers receive the 'conn' object as an argument and perform their operations directly on it.
#     # This pattern is acceptable because sync connections are blocking and expensive to open repeatedly.
#     # Using a shared connection per event keeps the logic efficient and transactionally consistent.
#     def _handle_event(self, data):
#         event_type = data.get("event_type")
#         handler = self.dispatch_map.get(event_type) #lookup to see which method needs to be run for eventtype
#         if handler:
#             try:
#                 with psycopg2.connect(self.database_url) as conn:
#                     handler(conn, data)
#                     conn.commit()
#             except Exception as e:
#                 self.logger.warning("[POSTGRES_SYNC] Failed to process event_type '%s': %s", event_type, e)
#                 raise
#         else:
#             self.logger.warning("[POSTGRES_SYNC] No handler for event_type: %s", event_type)

#     def _insert_rf_event(self, conn, data):
#         columns = sql_definitions.event_columns
#         values = []
#         for name, _ in columns:
#             # tags needs a different approach because it is a list and needs to be serialized to JSON
#             if name == "tags":
#                 tags = data.get(name, [])
#                 values.append(json.dumps(tags))  # serialize to JSON string
#             else:
#                 values.append(data.get(name))
#         conn.execute(sql_definitions.INSERT_EVENT, values)

#     def _insert_rf_log(self, conn, data):
#         columns = sql_definitions.rf_log_columns
#         values = [data.get(name) for name, _ in columns]
#         conn.execute(sql_definitions.INSERT_RF_LOG_MESSAGE, values)
