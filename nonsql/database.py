from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime, timedelta
import json
import time
from pathlib import Path
from threading import Lock
import hashlib
import zlib

class TimeBasedPartition:
    """Manages time-based data partitioning"""
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_partition_path(self, timestamp: float) -> Path:
        """Creates partition path based on timestamp"""
        dt = time.strftime("%Y-%m-%d-%H", time.localtime(timestamp))
        path = self.base_path / dt
        path.mkdir(exist_ok=True)
        return path

class BloomFilter:
    """Simple Bloom filter for quick membership testing"""
    def __init__(self, size: int = 10000, hash_funcs: int = 3):
        self.size = size
        self.hash_funcs = hash_funcs
        self.bit_array = [False] * size
        
    def _hash(self, item: str) -> List[int]:
        """Generate multiple hash values for an item"""
        h1 = int(hashlib.md5(str(item).encode()).hexdigest(), 16)
        h2 = int(hashlib.sha1(str(item).encode()).hexdigest(), 16)
        return [
            (h1 + i * h2) % self.size 
            for i in range(self.hash_funcs)
        ]
    
    def add(self, item: str):
        """Add item to Bloom filter"""
        for idx in self._hash(item):
            self.bit_array[idx] = True
    
    def might_contain(self, item: str) -> bool:
        """Check if item might be in the set"""
        return all(self.bit_array[idx] for idx in self._hash(item))

class DatabaseConfig:
    def __init__(self, 
                 db_path: str = "nonsql_data",
                 cache_size: int = 1000,
                 bloom_filter_size: int = 10000,
                 compression: bool = True,
                 default_ttl: Optional[int] = None,
                 hash_funcs: int = 3):
        self.db_path = db_path
        self.cache_size = cache_size
        self.bloom_filter_size = bloom_filter_size
        self.compression = compression
        self.default_ttl = default_ttl
        self.hash_funcs = hash_funcs

class Database:
    """
    A unique database implementation featuring:
    - Time-based data partitioning
    - Bloom filter for quick lookups
    - Memory cache with LRU eviction
    - JSON-based persistence
    - Automatic data versioning
    """
    
    def __init__(self, config: Union[str, DatabaseConfig] = "nonsql_data"):
        if isinstance(config, str):
            self.config = DatabaseConfig(db_path=config)
        else:
            self.config = config
            
        self.partition_manager = TimeBasedPartition(self.config.db_path)
        self.memory_cache: Dict[str, Any] = {}
        self.cache_max_size = self.config.cache_size
        self.bloom_filter = BloomFilter(self.config.bloom_filter_size, self.config.hash_funcs)
        self.lock = Lock()
        self.version_counter = 0
        self.indexes: Dict[str, Dict[str, List[str]]] = {}

    def create_index(self, field: str):
        """Create an index on a specific field"""
        self.indexes[field] = {}
        # Build index from existing documents
        for partition in self.partition_manager.base_path.glob("*"):
            for file_path in partition.glob("*.json"):
                with open(file_path, 'r') as f:
                    doc = json.load(f)
                    if field in doc["value"]:
                        field_value = str(doc["value"][field])
                        self.indexes[field].setdefault(field_value, []).append(doc["doc_id"])

    def _generate_key_hash(self, key: str) -> str:
        """Generate a unique hash for a key"""
        return hashlib.sha256(str(key).encode()).hexdigest()[:12]
    
    def _evict_cache_if_needed(self):
        """Evict oldest items if cache is too large"""
        if len(self.memory_cache) > self.cache_max_size:
            items_to_remove = len(self.memory_cache) - self.cache_max_size
            for _ in range(items_to_remove):
                self.memory_cache.pop(next(iter(self.memory_cache)))

    def _compress_data(self, data: dict) -> bytes:
        """Compress document data"""
        if self.config.compression:
            return zlib.compress(json.dumps(data).encode())
        return json.dumps(data).encode()

    def _decompress_data(self, data: bytes) -> dict:
        """Decompress document data"""
        if self.config.compression:
            return json.loads(zlib.decompress(data).decode())
        return json.loads(data.decode())

    def batch_insert(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents at once"""
        doc_ids = []
        with self.lock:
            for doc in documents:
                doc_id = self.insert(doc["key"], doc["value"], doc.get("tags"))
                doc_ids.append(doc_id)
        return doc_ids

    def insert(self, key: str, value: Any, tags: Optional[List[str]] = None, ttl: Optional[int] = None) -> str:
        """
        Insert a value with optional tags and versioning
        Returns: Document ID
        """
        with self.lock:
            timestamp = time.time()
            key_hash = self._generate_key_hash(key)
            
            document = {
                "key": key,
                "value": value,
                "tags": tags or [],
                "timestamp": timestamp,
                "version": self.version_counter,
                "doc_id": key_hash,
                "expires_at": time.time() + (ttl or self.config.default_ttl or 0) if (ttl or self.config.default_ttl) else None
            }
            
            # Update indexes
            for field, index in self.indexes.items():
                if field in value:
                    field_value = str(value[field])
                    index.setdefault(field_value, []).append(key_hash)

            # Compress and save
            compressed_data = self._compress_data(document)
            partition_path = self.partition_manager.get_partition_path(timestamp)
            file_path = partition_path / f"{key_hash}.dat"
            
            with open(file_path, 'wb') as f:
                f.write(compressed_data)

            self.memory_cache[key] = document
            self.bloom_filter.add(key)
            self._evict_cache_if_needed()
            
            self.version_counter += 1
            return key_hash
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value by key
        Returns: Document or None if not found
        """
        if not self.bloom_filter.might_contain(key):
            return None
            
        if key in self.memory_cache:
            doc = self.memory_cache[key]
            if doc.get("expires_at") and time.time() > doc["expires_at"]:
                self.delete(key)
                return None
            return doc

        key_hash = self._generate_key_hash(key)
        for partition in self.partition_manager.base_path.glob("*"):
            file_path = partition / f"{key_hash}.dat"
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    document = self._decompress_data(f.read())
                    if document.get("expires_at") and time.time() > document["expires_at"]:
                        self.delete(key)
                        return None
                    self.memory_cache[key] = document
                    self._evict_cache_if_needed()
                    return document
        
        return None
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Search documents by tags"""
        results = []
        seen_docs = set()
        
        # Search in memory cache
        for doc in self.memory_cache.values():
            if any(tag in doc["tags"] for tag in tags):
                results.append(doc)
                seen_docs.add(doc["doc_id"])
        
        # Search in partitions
        for partition in self.partition_manager.base_path.glob("*"):
            for file_path in partition.glob("*.json"):
                if file_path.stem not in seen_docs:
                    with open(file_path, 'r') as f:
                        doc = json.load(f)
                        if any(tag in doc["tags"] for tag in tags):
                            results.append(doc)
        
        return results
    
    def get_version_history(self, key: str) -> List[Dict[str, Any]]:
        """Get all versions of a document"""
        key_hash = self._generate_key_hash(key)
        versions = []
        
        for partition in self.partition_manager.base_path.glob("*"):
            file_path = partition / f"{key_hash}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    versions.append(json.load(f))
        
        return sorted(versions, key=lambda x: x["version"])
    
    def delete(self, key: str) -> bool:
        """Delete a document"""
        with self.lock:
            key_hash = self._generate_key_hash(key)
            deleted = False
            
            # Remove from cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
            
            # Remove from disk
            for partition in self.partition_manager.base_path.glob("*"):
                file_path = partition / f"{key_hash}.json"
                if file_path.exists():
                    file_path.unlink()
                    deleted = True
            
            return deleted

    def query_by_index(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Query documents using an index"""
        if field not in self.indexes:
            raise ValueError(f"No index exists for field: {field}")
            
        results = []
        value_str = str(value)
        if value_str in self.indexes[field]:
            for doc_id in self.indexes[field][value_str]:
                doc = self.get_by_doc_id(doc_id)
                if doc:
                    results.append(doc)
        return results

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[str]:
        """Update multiple documents atomically"""
        doc_ids = []
        timestamp = time.time()
        
        with self.lock:
            for update in updates:
                key = update["key"]
                new_value = update["value"]
                key_hash = self._generate_key_hash(key)
                
                # Prepare document
                if key in self.memory_cache:
                    existing_doc = self.memory_cache[key]
                    updated_value = existing_doc["value"].copy()
                    updated_value.update(new_value)
                    tags = existing_doc.get("tags", [])
                else:
                    updated_value = new_value
                    tags = []
                
                # Create new document
                document = {
                    "key": key,
                    "value": updated_value,
                    "tags": tags,
                    "timestamp": timestamp,
                    "version": self.version_counter,
                    "doc_id": key_hash,
                    "expires_at": None
                }
                
                # Save directly
                compressed_data = self._compress_data(document)
                partition_path = self.partition_manager.get_partition_path(timestamp)
                file_path = partition_path / f"{key_hash}.dat"
                
                with open(file_path, 'wb') as f:
                    f.write(compressed_data)
                
                # Update cache and indexes
                self.memory_cache[key] = document
                self.bloom_filter.add(key)
                
                for field, index in self.indexes.items():
                    if field in updated_value:
                        field_value = str(updated_value[field])
                        index.setdefault(field_value, []).append(key_hash)
                
                doc_ids.append(key_hash)
                self.version_counter += 1
            
            self._evict_cache_if_needed()
            
        return doc_ids

    def cleanup_expired(self) -> int:
        """Remove expired documents and return count of removed items"""
        removed = 0
        current_time = time.time()
        
        # Clean cache
        expired_keys = [k for k, v in self.memory_cache.items() 
                       if v.get("expires_at") and v["expires_at"] < current_time]
        for key in expired_keys:
            self.delete(key)
            removed += 1
            
        # Clean disk
        for partition in self.partition_manager.base_path.glob("*"):
            for file_path in partition.glob("*.dat"):
                with open(file_path, 'rb') as f:
                    doc = self._decompress_data(f.read())
                    if doc.get("expires_at") and doc["expires_at"] < current_time:
                        file_path.unlink()
                        removed += 1
                        
        return removed



