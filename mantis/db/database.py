import os
from mantis.config_parsers.config_client import ConfigProvider
import motor.motor_asyncio

# MANTIS_MONGO_URI lets deployments inject credentials without baking them into local.yml
mongo_db_connction = os.environ.get("MANTIS_MONGO_URI") or ConfigProvider.get_config().dbConfig.mongoConnectionString
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_db_connction)

database = client.mantis

assets_collection = database.get_collection("assets_collection")
findings_collection = database.get_collection("findings_collection")
extended_assets_collection = database.get_collection("extended_assets_collection")
