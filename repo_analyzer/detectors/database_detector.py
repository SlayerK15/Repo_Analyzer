"""
Database Detector module for identifying database technologies used in a repository.

This module analyzes file content to detect database technologies by looking for:
1. Connection strings and URLs
2. Database driver imports and dependencies
3. ORM (Object-Relational Mapping) patterns
4. SQL query patterns and database-specific syntax
5. Configuration files for database services
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any

class DatabaseDetector:
    """
    Detector for database technologies used in a repository.
    
    This class examines code and configuration files to identify database
    technologies used in the codebase, such as SQL and NoSQL databases.
    It detects databases by looking for connection strings, drivers,
    ORM patterns, and query syntax.
    """
    
    def __init__(self):
        """Initialize the Database Detector with database detection patterns."""
        # Database URL patterns
        self.db_url_patterns = {
            "MySQL": [
                r"mysql://", r"jdbc:mysql", r"mysql://[a-zA-Z0-9:@\.\-_]+/[a-zA-Z0-9_]+",
                r"host\s*=\s*['\"].*?['\"].*?database\s*=\s*['\"].*?['\"]",
                r"(?:DB_HOST|MYSQL_HOST)"
            ],
            "PostgreSQL": [
                r"postgres(?:ql)?://", r"jdbc:postgresql", r"psql://", 
                r"postgres(?:ql)?://[a-zA-Z0-9:@\.\-_]+/[a-zA-Z0-9_]+",
                r"(?:DB_HOST|POSTGRES_HOST)"
            ],
            "SQLite": [
                r"sqlite:///", r"jdbc:sqlite", r"\.db(?:3)?['\"]",
                r"(?:DB_PATH|SQLITE_DATABASE)"
            ],
            "MongoDB": [
                r"mongodb(?:\+srv)?://", r"mongodb(?:\+srv)?://[a-zA-Z0-9:@\.\-_]+/[a-zA-Z0-9_]+",
                r"(?:MONGO_URI|MONGODB_URI)"
            ],
            "Redis": [
                r"redis://", r"redis://[a-zA-Z0-9:@\.\-_]+(?::[0-9]+)?",
                r"(?:REDIS_URL|REDIS_HOST)"
            ],
            "Oracle": [
                r"oracle://", r"jdbc:oracle", r"sid\s*=\s*['\"].*?['\"]",
                r"(?:ORACLE_SID|ORACLE_HOST)"
            ],
            "SQL Server": [
                r"mssql://", r"jdbc:sqlserver", r"sqlserver://",
                r"(?:MSSQL_HOST|SQL_SERVER)"
            ],
            "Cassandra": [
                r"cassandra://", r"jdbc:cassandra", r"contactPoints\s*="
            ],
            "Elasticsearch": [
                r"elasticsearch://", r"http[s]?://[a-zA-Z0-9\.\-_]+:9200"
            ],
            "DynamoDB": [
                r"dynamodb://", r"aws_access_key_id.*?aws_secret_access_key",
                r"AWS::DynamoDB"
            ],
            "Firebase": [
                r"firebaseio\.com", r"apiKey.*?authDomain.*?databaseURL",
                r"firebase\.initializeApp"
            ],
            "Neo4j": [
                r"neo4j://", r"bolt://", r"jdbc:neo4j"
            ]
        }
        
        # Database driver import patterns
        self.db_driver_patterns = {
            "MySQL": [
                r"mysql\.connector", r"pymysql", r"import\s+mysql", r"require\(['\"]mysql['\"]",
                r"gem ['\"]mysql2['\"]", r"jdbc/mysql", r"MySqlClient", r"MySqlConnection"
            ],
            "PostgreSQL": [
                r"import\s+psycopg2", r"require\(['\"]pg['\"]", r"gem ['\"]pg['\"]",
                r"jdbc/postgresql", r"PostgresClient", r"PostgresConnection", r"Npgsql",
                r"import\s+pg", r"from\s+pg\s+import"
            ],
            "SQLite": [
                r"import\s+sqlite3", r"require\(['\"]sqlite3['\"]", r"gem ['\"]sqlite3['\"]",
                r"jdbc/sqlite", r"SqliteConnection", r"SqliteDatabase"
            ],
            "MongoDB": [
                r"import\s+pymongo", r"from\s+pymongo", r"require\(['\"]mongodb['\"]",
                r"mongoose", r"MongoClient", r"MongoDatabase", r"MongoDB\."
            ],
            "Redis": [
                r"import\s+redis", r"from\s+redis", r"require\(['\"]redis['\"]",
                r"gem ['\"]redis['\"]", r"RedisClient", r"createClient\(\)"
            ],
            "Oracle": [
                r"import\s+cx_Oracle", r"require\(['\"]oracledb['\"]",
                r"gem ['\"]ruby-oci8['\"]", r"jdbc/oracle", r"OracleConnection"
            ],
            "SQL Server": [
                r"import\s+pyodbc", r"import\s+pymssql", r"require\(['\"]mssql['\"]",
                r"jdbc/sqlserver", r"SqlConnection", r"SqlClient"
            ],
            "Cassandra": [
                r"import\s+cassandra", r"from\s+cassandra", r"require\(['\"]cassandra['\"]",
                r"CassandraClient", r"CassandraCluster"
            ],
            "Elasticsearch": [
                r"import\s+elasticsearch", r"from\s+elasticsearch", 
                r"require\(['\"]elasticsearch['\"]", r"ElasticsearchClient"
            ],
            "DynamoDB": [
                r"import\s+boto3", r"from\s+boto3", r"DynamoDBClient",
                r"AWS\.DynamoDB", r"DocumentClient"
            ],
            "Firebase": [
                r"import\s+firebase", r"from\s+firebase", r"require\(['\"]firebase['\"]",
                r"FirebaseDatabase", r"initializeApp"
            ],
            "Neo4j": [
                r"import\s+neo4j", r"from\s+neo4j", r"require\(['\"]neo4j['\"]",
                r"Neo4jClient", r"Neo4jDriver"
            ]
        }
        
        # ORM patterns
        self.orm_patterns = {
            "SQLAlchemy (Python)": [
                r"import\s+sqlalchemy", r"from\s+sqlalchemy", r"create_engine\(",
                r"Column\(", r"relationship\(", r"Base\s*=\s*declarative_base\(\)"
            ],
            "Django ORM (Python)": [
                r"from\s+django\.db\s+import\s+models", r"class\s+\w+\(models\.Model\)",
                r"models\.\w+Field\("
            ],
            "Sequelize (JavaScript)": [
                r"const\s+sequelize\s*=\s*new\s+Sequelize", r"import\s+Sequelize",
                r"sequelize\.define\(", r"DataTypes\."
            ],
            "TypeORM (TypeScript)": [
                r"import\s+{\s*Entity", r"@Entity\(", r"@Column\(", r"@ManyToOne",
                r"@OneToMany", r"createConnection\("
            ],
            "Hibernate (Java)": [
                r"import\s+javax\.persistence", r"import\s+org\.hibernate",
                r"@Entity", r"@Table", r"@Column", r"SessionFactory"
            ],
            "Prisma (JavaScript/TypeScript)": [
                r"import\s+{\s*PrismaClient", r"const\s+prisma\s*=\s*new\s+PrismaClient",
                r"prisma\.\w+\.findMany", r"prisma\.\w+\.create"
            ],
            "Entity Framework (C#)": [
                r"using\s+Microsoft\.EntityFrameworkCore", r"DbContext",
                r"DbSet<", r"OnModelCreating"
            ],
            "Mongoose (JavaScript)": [
                r"import\s+mongoose", r"const\s+mongoose\s*=\s*require\(['\"]mongoose['\"]\)",
                r"mongoose\.Schema", r"mongoose\.model\("
            ],
            "ActiveRecord (Ruby)": [
                r"class\s+\w+\s*<\s*ApplicationRecord", r"class\s+\w+\s*<\s*ActiveRecord::Base",
                r"has_many\s+:", r"belongs_to\s+:"
            ],
            "GORM (Go)": [
                r"import\s+\"gorm\.io/gorm\"", r"db\s*:=\s*gorm\.Open\(",
                r"type\s+\w+\s+struct\s+{[\s\S]*?`gorm:"
            ]
        }
        
        # Query syntax patterns
        self.query_patterns = {
            "SQL": [
                r"SELECT\s+[\w\*]+\s+FROM\s+\w+", r"INSERT\s+INTO\s+\w+",
                r"UPDATE\s+\w+\s+SET", r"DELETE\s+FROM\s+\w+", 
                r"CREATE\s+TABLE\s+\w+", r"ALTER\s+TABLE\s+\w+"
            ],
            "MySQL-specific": [
                r"SHOW\s+DATABASES", r"SHOW\s+TABLES", r"ENGINE\s*=\s*InnoDB"
            ],
            "PostgreSQL-specific": [
                r"CREATE\s+EXTENSION", r"::jsonb", r"WITH\s+RECURSIVE"
            ],
            "MongoDB Query": [
                r"\{\s*\$match", r"\{\s*\$group", r"\{\s*\$lookup", 
                r"\.find\(\{", r"\.aggregate\(\["
            ],
            "Elasticsearch Query": [
                r"\"query\":\s*\{", r"\"bool\":\s*\{", r"\"must\":\s*\[",
                r"\"match\":\s*\{", r"\"term\":\s*\{"
            ],
            "GraphQL": [
                r"query\s*\{", r"mutation\s*\{", r"type\s+\w+\s*\{",
                r"fragment\s+\w+\s+on"
            ]
        }
        
        # Configuration file patterns
        self.config_file_patterns = {
            "MySQL": [
                r"my\.cnf", r"mysql-config", r"mysqld\.conf"
            ],
            "PostgreSQL": [
                r"pg_hba\.conf", r"postgresql\.conf", r"postgres\.(json|yaml|yml)"
            ],
            "SQLite": [
                r"\.sqlite3?-journal", r"\.db-journal"
            ],
            "MongoDB": [
                r"mongod\.conf", r"mongo\.(json|yaml|yml)"
            ],
            "Redis": [
                r"redis\.conf", r"redis\.(json|yaml|yml)"
            ],
            "Elasticsearch": [
                r"elasticsearch\.yml", r"elastic\.(json|yaml|yml)"
            ],
            "Cassandra": [
                r"cassandra\.yaml", r"cassandra-env\.sh"
            ]
        }
    
    def detect(self, files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect database technologies used in the repository.
        
        This method analyzes file content to identify database technologies by
        looking for connection strings, driver imports, ORM patterns, query syntax,
        and configuration files.
        
        Args:
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict mapping database technology names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
                - evidence: List of evidence found (up to 5 examples)
        """
        # Track matches for each database technology
        db_matches = defaultdict(int)
        evidence = defaultdict(list)
        
        # Regular expressions for each pattern type
        for file_path, content in files_content.items():
            filename = os.path.basename(file_path)
            
            # Check for configuration files
            for db, config_patterns in self.config_file_patterns.items():
                for pattern in config_patterns:
                    if re.search(pattern, filename, re.IGNORECASE):
                        db_matches[db] += 20  # High weight for config files
                        evidence[db].append(f"Config file: {filename}")
            
            # Skip very large files for content analysis
            if len(content) > 500000:  # Skip files larger than 500KB
                continue
            
            # Check for database URLs and connection strings
            for db, url_patterns in self.db_url_patterns.items():
                for pattern in url_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Add weight based on number of matches
                        db_matches[db] += len(matches) * 10
                        # Add first match as evidence (obfuscate any actual credentials)
                        match_text = matches[0]
                        if len(match_text) > 60:  # Truncate long matches
                            match_text = match_text[:57] + "..."
                        # Obfuscate potential credentials
                        obfuscated = re.sub(r'://[^@/]+@', '://***@', match_text)
                        evidence[db].append(f"Connection string: {obfuscated}")
            
            # Check for database driver imports
            for db, driver_patterns in self.db_driver_patterns.items():
                for pattern in driver_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        db_matches[db] += len(matches) * 8
                        evidence[db].append(f"Driver: {matches[0]}")
            
            # Check for ORM patterns
            for orm, orm_patterns in self.orm_patterns.items():
                for pattern in orm_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Extract the database name from the ORM name
                        if "SQLAlchemy" in orm:
                            # SQLAlchemy could be used with multiple databases
                            # Check for specific database engines
                            if "mysql" in content.lower():
                                db_matches["MySQL"] += len(matches) * 5
                                evidence["MySQL"].append(f"ORM ({orm}): {matches[0]}")
                            if "postgres" in content.lower():
                                db_matches["PostgreSQL"] += len(matches) * 5
                                evidence["PostgreSQL"].append(f"ORM ({orm}): {matches[0]}")
                            if "sqlite" in content.lower():
                                db_matches["SQLite"] += len(matches) * 5
                                evidence["SQLite"].append(f"ORM ({orm}): {matches[0]}")
                        elif "Django ORM" in orm:
                            # Django ORM defaults to SQLite but can use others
                            # Look for database settings
                            if "postgresql" in content.lower() or "psycopg2" in content.lower():
                                db_matches["PostgreSQL"] += len(matches) * 5
                                evidence["PostgreSQL"].append(f"ORM ({orm}): {matches[0]}")
                            elif "mysql" in content.lower():
                                db_matches["MySQL"] += len(matches) * 5
                                evidence["MySQL"].append(f"ORM ({orm}): {matches[0]}")
                            else:
                                db_matches["SQLite"] += len(matches) * 5
                                evidence["SQLite"].append(f"ORM ({orm}): {matches[0]}")
                        elif "Mongoose" in orm:
                            db_matches["MongoDB"] += len(matches) * 5
                            evidence["MongoDB"].append(f"ORM ({orm}): {matches[0]}")
                        elif "Sequelize" in orm or "Prisma" in orm:
                            # Check for specific database configuration
                            if "postgres" in content.lower():
                                db_matches["PostgreSQL"] += len(matches) * 5
                                evidence["PostgreSQL"].append(f"ORM ({orm}): {matches[0]}")
                            else:
                                db_matches["MySQL"] += len(matches) * 5
                                evidence["MySQL"].append(f"ORM ({orm}): {matches[0]}")
                        elif "Hibernate" in orm or "Entity Framework" in orm:
                            # These ORMs are commonly used with various SQL databases
                            # Add a generic match for multiple possible databases
                            db_matches["SQL Database"] += len(matches) * 3
                            evidence["SQL Database"].append(f"ORM ({orm}): {matches[0]}")
                        elif "ActiveRecord" in orm:
                            db_matches["PostgreSQL"] += len(matches) * 3
                            evidence["PostgreSQL"].append(f"ORM ({orm}): {matches[0]}")
                            db_matches["MySQL"] += len(matches) * 2
                            evidence["MySQL"].append(f"ORM ({orm}): {matches[0]}")
                        elif "GORM" in orm:
                            db_matches["PostgreSQL"] += len(matches) * 3
                            evidence["PostgreSQL"].append(f"ORM ({orm}): {matches[0]}")
            
            # Check for query syntax patterns
            for db_type, query_patterns in self.query_patterns.items():
                for pattern in query_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Map query syntax to database types
                        if db_type == "SQL":
                            # Generic SQL could be any SQL database
                            # Add smaller weights to common SQL databases
                            db_matches["SQL Database"] += len(matches) * 2
                            evidence["SQL Database"].append(f"SQL Query: {matches[0][:40]}...")
                        elif db_type == "MySQL-specific":
                            db_matches["MySQL"] += len(matches) * 5
                            evidence["MySQL"].append(f"MySQL Query: {matches[0][:40]}...")
                        elif db_type == "PostgreSQL-specific":
                            db_matches["PostgreSQL"] += len(matches) * 5
                            evidence["PostgreSQL"].append(f"PostgreSQL Query: {matches[0][:40]}...")
                        elif db_type == "MongoDB Query":
                            db_matches["MongoDB"] += len(matches) * 5
                            evidence["MongoDB"].append(f"MongoDB Query: {matches[0][:40]}...")
                        elif db_type == "Elasticsearch Query":
                            db_matches["Elasticsearch"] += len(matches) * 5
                            evidence["Elasticsearch"].append(f"Elasticsearch Query: {matches[0][:40]}...")
                        elif db_type == "GraphQL":
                            # GraphQL is not a database itself, but is often used with specific databases
                            db_matches["GraphQL"] += len(matches) * 3
                            evidence["GraphQL"].append(f"GraphQL: {matches[0][:40]}...")
        
        # Calculate confidence scores and prepare results
        databases = {}
        
        if db_matches:
            # Find the maximum number of matches to normalize scores
            max_matches = max(db_matches.values())
            
            for db, matches in db_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_matches) * 100)
                
                # Only include databases with reasonable confidence
                if confidence >= 15:  # Higher threshold for databases to reduce false positives
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(set(evidence[db]))[:5]
                    
                    databases[db] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        return databases