import logging
import logging.handlers
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback
from core import database as db
import models as DBmodels
from sqlalchemy.orm import Session

# Log file in backend directory
LOG_FILE = Path(__file__).parent / "logfile.txt"

class DatabaseLogHandler(logging.Handler):
    """Custom logging handler that writes to database"""
    
    def emit(self, record: logging.LogRecord):
        try:
            # Get database session
            session = db.SessionLocal()
            try:
                # Extract request information if available
                request_method = getattr(record, 'request_method', None)
                request_path = getattr(record, 'request_path', None)
                request_ip = getattr(record, 'request_ip', None)
                response_status = getattr(record, 'response_status', None)
                
                # Get exception info if available
                exception_info = None
                if record.exc_info:
                    exception_info = ''.join(traceback.format_exception(*record.exc_info))
                
                # Create log entry
                log_entry = DBmodels.Log(
                    timestamp=datetime.utcnow(),
                    level=record.levelname,
                    logger_name=record.name,
                    message=self.format(record),
                    module=record.module,
                    function=record.funcName,
                    line_number=record.lineno,
                    request_method=request_method,
                    request_path=request_path,
                    request_ip=request_ip,
                    response_status=response_status,
                    exception=exception_info
                )
                
                session.add(log_entry)
                session.commit()
            except Exception as e:
                session.rollback()
                # Fallback to console if database logging fails
                print(f"Failed to write log to database: {e}", file=sys.stderr)
            finally:
                session.close()
        except Exception:
            # Prevent logging errors from breaking the application
            pass


class FileAndDatabaseHandler(logging.Handler):
    """Handler that writes to both file and database"""
    
    def __init__(self):
        super().__init__()
        # Use RotatingFileHandler: 5MB max size, keep 5 backups
        self.file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, 
            maxBytes=5 * 1024 * 1024, 
            backupCount=5, 
            encoding='utf-8'
        )
        self.file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.db_handler = DatabaseLogHandler()
        self.db_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
    
    def emit(self, record: logging.LogRecord):
        # Write to file
        self.file_handler.emit(record)
        # Write to database
        self.db_handler.emit(record)
    
    def close(self):
        self.file_handler.close()
        self.db_handler.close()
        super().close()

def setup_logging():
    """Configure logging for the application"""
    
    # Create custom handler
    handler = FileAndDatabaseHandler()
    handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Suppress noise from various libraries
    for name in ["qiskit", "stevedore", "matplotlib", "concurrent", "asyncio", "httpcore", "httpx", "google", "langchain", "pydantic"]:
         logging.getLogger(name).setLevel(logging.WARNING)

    # Specific suppression for schema warnings and version warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")
    # Pydantic schema noise can sometimes be stubborn, so we explicitly set it to ERROR if WARNING isn't enough
    logging.getLogger("pydantic").setLevel(logging.ERROR)
        
    # Log initial message
    logging.info("Logging system initialized - writing to both logfile.txt (rotated) and database logtable")

