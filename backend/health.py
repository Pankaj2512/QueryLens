"""Health check and monitoring utilities."""
import logging
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import text
from models import engine, SessionLocal

logger = logging.getLogger(__name__)


class HealthChecker:
    """Performs health checks on various system components."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            db = SessionLocal()
            # Simple query to verify connection
            db.execute(text("SELECT 1"))
            db.close()
            return {
                "status": "healthy",
                "component": "database",
                "message": "Database connection successful",
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "component": "database",
                "message": f"Database connection failed: {str(e)}",
                "error": str(e),
            }

    @staticmethod
    def check_file_system() -> Dict[str, Any]:
        """Check file system access."""
        try:
            from pathlib import Path
            from database import DATA_DIR
            
            # Check if upload directory exists and is writable
            if not DATA_DIR.exists():
                DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Try to write a test file
            test_file = DATA_DIR / ".health_check"
            test_file.touch()
            test_file.unlink()
            
            return {
                "status": "healthy",
                "component": "file_system",
                "message": "File system access successful",
            }
        except Exception as e:
            logger.error(f"File system health check failed: {e}")
            return {
                "status": "unhealthy",
                "component": "file_system",
                "message": f"File system access failed: {str(e)}",
                "error": str(e),
            }

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get system metrics."""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except ImportError:
            logger.warning("psutil not installed, skipping system metrics")
            return {}
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    @staticmethod
    def full_health_check() -> Dict[str, Any]:
        """Perform full health check."""
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {
                "database": HealthChecker.check_database(),
                "file_system": HealthChecker.check_file_system(),
            },
        }
        
        # Add system metrics
        metrics = HealthChecker.get_system_metrics()
        if metrics:
            checks["system_metrics"] = metrics
        
        # Determine overall status
        for component in checks["components"].values():
            if component["status"] == "unhealthy":
                checks["overall_status"] = "degraded"
                break
        
        return checks


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    try:
        from database import get_tables
        
        db = SessionLocal()
        tables = get_tables()
        
        stats = {
            "total_tables": len(tables),
            "tables": tables,
        }
        
        # Get row counts for each table
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                row = result.fetchone()
                count = row[0] if row else 0
                stats[f"{table}_rows"] = count
            except Exception as e:
                logger.warning(f"Could not get row count for {table}: {e}")
        
        db.close()
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {"error": str(e)}
