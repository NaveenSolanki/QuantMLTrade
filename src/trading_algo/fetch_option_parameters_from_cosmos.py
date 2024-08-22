from azure.cosmos import CosmosClient

class cosmosDB_items:
    def __init__(self):    
        # Initialize the Cosmos client
        self.endpoint = 'https://azure-db-cosmos.documents.azure.com:443/'
        self.key = 'wqJhec9iuu7z6EjdTtphg9pvvHt8TqwoW03LRnlkl3Rd9083kagOKoXlcNmACDbq3z0pQ=='
        # Select the database and container
        self.database_name = 'option_pattern_trading_algo'
        self.container_name = 'pe_or_ce'
        # Initialize the Cosmos client
        self.client = CosmosClient(self.endpoint, self.key)

        # Select the database and container
        self.database = self.client.get_database_client(self.database_name)
        self.container = self.database.get_container_client(self.container_name)
        
    def fetch_option_parameters_from_cosmos(self):
        # Query the container to fetch items
        query = None
        if query is None:
            # Query the container to fetch items
            query = "SELECT * FROM c WHERE c.status = 'active' ORDER BY c._ts ASC"

        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

        # Check if there are any active items
        if items:
            # Get the first active item
            first_active_item = items[0]
            return first_active_item
        else:
            return None
    
    def update_option_parameters_status(self, item_id):
        # Retrieve the item by ID
        item = self.container.read_item(item=item_id, partition_key=item_id)

        # Update the status of the item to "inactive"
        item['status'] = 'inactive'

        # Replace the item in the container with the updated item
        self.container.replace_item(item=item_id, body=item)
        
# print(cosmosDB_items().fetch_option_parameters_from_cosmos())
# print(type(fetch_option_parameters_from_sql()))