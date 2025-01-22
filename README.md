# NoSQL Database

NonSQL is a Python-based, feature-rich NoSQL database designed for quick development and local storage needs. It supports time-based partitioning, memory caching, bloom filters, and more to provide an efficient and scalable solution for small-scale projects.

---


## Features

| Feature                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **Time-Based Partitioning**      | Organizes data into directories based on timestamps for efficient storage. |
| **Bloom Filter**                 | Enables fast membership tests, minimizing unnecessary disk I/O.            |
| **LRU Cache**                    | In-memory cache for frequently accessed documents with eviction policies.  |
| **Document Compression**         | Optional zlib compression for optimized storage.                           |
| **Batch Operations**             | Support for batch inserts and updates.                                     |
| **Indexing**                     | Create indexes on fields for fast lookups and queries.                     |
| **TTL and Expiry**               | Automatically remove expired documents.                                     |
| **Versioning**                   | Tracks multiple versions of documents for history retrieval.               |


---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
    - [Initialization](#initialization)
    - [Developer](#developer)
    - [Insert Document](#insert-document)
    - [Retrieve Document](#retrieve-document)
    - [Batch Insert](#batch-insert)
    - [Update Document](#update-document)
    - [Search by Tags](#search-by-tags)
    - [Create Index](#create-index)
    - [Query by Index](#query-by-index)
    - [Version History](#version-history)
    - [Cleanup Expired Documents](#cleanup-expired-documents)
3. [CLI](#cli)
4. [Configuration Options](#configuration-options)
5. [Examples](#examples)
    - [User Management System](#user-management-system)
    - [Inventory Management System](#inventory-management-system)
    - [Like Collection System](#like-collection-system)
    - [Real-Time Analytics System](#real-time-analytics-system)
    - [Advanced Time-Series Analytics System](#advanced-time-series-analytics-system)
6. [License](#license)

---

## Installation

```bash
pip install nonsql
```

## Developer
* ishan oshada - [GitHub](https://github.com/ishanoshada)

---

## Usage

### Initialization

```python
from nonsql import Database, DatabaseConfig

# Default configuration
db = Database()

# Custom configuration
config = DatabaseConfig(
     db_path="my_data",
     cache_size=2000,
     bloom_filter_size=20000,
     compression=True,
     default_ttl=3600  # Documents expire in 1 hour by default
)
db = Database(config)
```

### Insert Document

```python
doc_id = db.insert(key="user123", value={"name": "John", "age": 30}, tags=["user", "active"])
print("Inserted Document ID:", doc_id)
```

### Retrieve Document

```python
document = db.get("user123")
if document:
     print("Document:", document)
else:
     print("Document not found or expired.")
```

### Batch Insert

```python
documents = [
     {"key": "user124", "value": {"name": "Jane", "age": 25}, "tags": ["user"]},
     {"key": "user125", "value": {"name": "Alice", "age": 28}, "tags": ["user"]},
]
doc_ids = db.batch_insert(documents)
print("Inserted Document IDs:", doc_ids)
```

### Update Document

```python
doc_id = db.insert(key="user123", value={"name": "John", "age": 30})
db.batch_update([
     {"key": "user123", "value": {"age": 31, "location": "NYC"}}
])
print("Document updated")
```

### Search by Tags

```python
results = db.search_by_tags(["user", "active"])
for result in results:
     print(result)
```

### Create Index

```python
db.create_index("age")
```

### Query by Index

```python
results = db.query_by_index("age", 30)
for result in results:
     print(result)
```

### Version History

```python
history = db.get_version_history("user123")
for version in history:
     print(version)
```

### Cleanup Expired Documents

```python
removed_count = db.cleanup_expired()
print(f"Removed {removed_count} expired documents.")
```

---

## Configuration Options

| Parameter           | Type       | Default        | Description                                   |
|---------------------|------------|----------------|-----------------------------------------------|
| `db_path`           | `str`      | `"nonsql_data"`| Directory path for storing data.             |
| `cache_size`        | `int`      | `1000`         | Maximum number of items in memory cache.     |
| `bloom_filter_size` | `int`      | `10000`        | Size of the Bloom filter.                    |
| `compression`       | `bool`     | `True`         | Enable/disable zlib compression for documents.|
| `default_ttl`       | `Optional[int]` | `None`    | Default Time-to-Live for documents (in seconds).|
| `hash_funcs`        | `int`      | `3`            | Number of hash functions for the Bloom filter.|

---
## CLI

The NonSQL database comes with a command-line interface for common operations.

### Basic Commands

```bash
# Initialize a new database
nonsql init path/to/db --config config.yaml

# Insert a document
nonsql insert path/to/db my_key '{"name": "John"}' --tags tag1 tag2

# Retrieve a document
nonsql get path/to/db my_key

# Delete a document
nonsql delete path/to/db my_key

# Create an index
nonsql create-index path/to/db field_name

# Search by tags
nonsql search path/to/db tag1 tag2

# Remove expired documents
nonsql cleanup path/to/db

# Get document history
nonsql history path/to/db my_key
```

### Example Config File (YAML)

```yaml
db_path: "my_database"
cache_size: 1000
bloom_filter_size: 10000
compression: true
default_ttl: 3600
```

## Examples

### Example Systems

#### User Management System

```python
from nonsql import Database, DatabaseConfig

# Custom configuration for user management
config = DatabaseConfig(
    db_path="user_data",
    cache_size=500,
    bloom_filter_size=5000,
    compression=True,
    default_ttl=7200  # Documents expire in 2 hours by default
)
db = Database(config)

# Insert user documents
db.insert(key="user001", value={"name": "Alice", "role": "admin"}, tags=["user", "admin"])
db.insert(key="user002", value={"name": "Bob", "role": "user"}, tags=["user", "active"])

# Retrieve a user document
user = db.get("user001")
print("User:", user)

# Update a user document
db.batch_update([{"key": "user002", "value": {"role": "moderator"}}])
print("User updated")

# Search users by tags
active_users = db.search_by_tags(["active"])
print("Active Users:", active_users)
```

#### Inventory Management System

```python
from nonsql import Database, DatabaseConfig

# Custom configuration for inventory management
config = DatabaseConfig(
    db_path="inventory_data",
    cache_size=1000,
    bloom_filter_size=10000,
    compression=True,
    default_ttl=86400  # Documents expire in 24 hours by default
)
db = Database(config)

# Insert product documents
db.insert(key="product001", value={"name": "Laptop", "quantity": 50}, tags=["electronics", "inventory"])
db.insert(key="product002", value={"name": "Smartphone", "quantity": 200}, tags=["electronics", "inventory"])

# Retrieve a product document
product = db.get("product001")
print("Product:", product)

# Update a product document
db.batch_update([{"key": "product002", "value": {"quantity": 180}}])
print("Product updated")

# Search products by tags
electronics = db.search_by_tags(["electronics"])
print("Electronics:", electronics)
```
#### Like Collection System

```python
from nonsql import Database, DatabaseConfig

# Custom configuration for like collection
config = DatabaseConfig(
    db_path="like_data",
    cache_size=300,
    bloom_filter_size=3000,
    compression=True,
    default_ttl=604800  # Documents expire in 7 days by default
)
db = Database(config)

# Insert like documents
db.insert(key="like001", value={"user_id": "user123", "item_id": "post456"}, tags=["like", "post"])
db.insert(key="like002", value={"user_id": "user124", "item_id": "post789"}, tags=["like", "post"])

# Retrieve a like document
like = db.get("like001")
print("Like:", like)

# Update a like document
db.batch_update([{"key": "like002", "value": {"item_id": "post101"}}])
print("Like updated")

# Search likes by tags
post_likes = db.search_by_tags(["post"])
print("Post Likes:", post_likes)
```

#### Real-Time Analytics System

```python
from nonsql import Database, DatabaseConfig

# Custom configuration for real-time analytics
config = DatabaseConfig(
    db_path="analytics_data",
    cache_size=5000,
    bloom_filter_size=50000,
    compression=True,
    default_ttl=3600  # Documents expire in 1 hour by default
)
db = Database(config)

# Insert event documents
db.insert(key="event001", value={"user_id": "user123", "action": "click", "timestamp": 1633072800}, tags=["event", "click"])
db.insert(key="event002", value={"user_id": "user124", "action": "view", "timestamp": 1633072900}, tags=["event", "view"])

# Retrieve an event document
event = db.get("event001")
print("Event:", event)

# Update an event document
db.batch_update([{"key": "event002", "value": {"action": "click"}}])
print("Event updated")

# Search events by tags
click_events = db.search_by_tags(["click"])
print("Click Events:", click_events)

# Aggregate events by action
from collections import Counter

events = db.search_by_tags(["event"])
action_counts = Counter(event["value"]["action"] for event in events)
print("Action Counts:", action_counts)
```

#### Advanced Time-Series Analytics System

```python
from nonsql import Database, DatabaseConfig
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

# Configuration optimized for time-series data
config = DatabaseConfig(
    db_path="timeseries_data",
    cache_size=10000,
    bloom_filter_size=100000,
    compression=True,
    default_ttl=2592000  # 30 days retention
)
db = Database(config)

# Complex time-series data insertion with multiple metrics
def insert_metric_batch(metrics, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    
    batch_data = []
    for sensor_id, values in metrics.items():
        key = f"sensor_{sensor_id}_{timestamp.timestamp()}"
        processed_values = {
            "raw": values,
            "stats": {.....................
```



## License

This project is licensed under the MIT License. See the LICENSE file for details.



**Repository Views** ![Views](https://profile-counter.glitch.me/nonsql/count.svg)