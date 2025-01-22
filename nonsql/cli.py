import click
import yaml
from .database import Database, DatabaseConfig
import json

@click.group()
def main():
    """NonSQL Database Management CLI"""
    pass

@main.command()
@click.argument('db_path')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file')
def init(db_path, config):
    """Initialize a new database"""
    if config:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
            db_config = DatabaseConfig(**config_data)
    else:
        db_config = DatabaseConfig(db_path=db_path)
    
    db = Database(db_config)
    click.echo(f"Database initialized at {db_path}")

@main.command()
@click.argument('db_path')
@click.argument('key')
@click.argument('value')
@click.option('--tags', '-t', multiple=True, help='Tags for the document')
def insert(db_path, key, value, tags):
    """Insert a document into the database"""
    db = Database(db_path)
    try:
        value_dict = json.loads(value)
        doc_id = db.insert(key, value_dict, list(tags))
        click.echo(f"Document inserted with ID: {doc_id}")
    except json.JSONDecodeError:
        click.echo("Error: Value must be valid JSON")

@main.command()
@click.argument('db_path')
@click.argument('key')
def get(db_path, key):
    """Retrieve a document by key"""
    db = Database(db_path)
    doc = db.get(key)
    if doc:
        click.echo(json.dumps(doc, indent=2))
    else:
        click.echo("Document not found")

@main.command()
@click.argument('db_path')
@click.argument('key')
def delete(db_path, key):
    """Delete a document by key"""
    db = Database(db_path)
    if db.delete(key):
        click.echo("Document deleted successfully")
    else:
        click.echo("Document not found")

@main.command()
@click.argument('db_path')
@click.argument('field')
def create_index(db_path, field):
    """Create an index on a field"""
    db = Database(db_path)
    db.create_index(field)
    click.echo(f"Index created on field: {field}")

@main.command()
@click.argument('db_path')
@click.argument('tags', nargs=-1)
def search(db_path, tags):
    """Search documents by tags"""
    db = Database(db_path)
    results = db.search_by_tags(list(tags))
    for doc in results:
        click.echo(json.dumps(doc, indent=2))

@main.command()
@click.argument('db_path')
def cleanup(db_path):
    """Remove expired documents"""
    db = Database(db_path)
    count = db.cleanup_expired()
    click.echo(f"Removed {count} expired documents")

@main.command()
@click.argument('db_path')
@click.argument('key')
def history(db_path, key):
    """Get version history of a document"""
    db = Database(db_path)
    versions = db.get_version_history(key)
    for version in versions:
        click.echo(json.dumps(version, indent=2))

if __name__ == '__main__':
    main()