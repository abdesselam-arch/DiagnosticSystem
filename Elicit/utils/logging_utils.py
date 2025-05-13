"""
Diagnostic Collection System - Logging Utilities

This module provides utilities for consistent logging throughout the
diagnostic collection system, with support for different log levels,
file rotation, and specialized loggers for system components.
"""

import os
import sys
import logging
import logging.handlers
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union


# Default logging format with timestamp, level, and message
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default date format for log entries
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels mapping for easier configuration
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "info",
    console: bool = True,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up a logger with specified handlers and formatting.
    
    Args:
        name (str): Logger name, typically the module name.
        log_file (str, optional): Path to log file. If None, file logging is disabled.
        level (str, optional): Log level ("debug", "info", "warning", "error", "critical").
                              Defaults to "info".
        console (bool, optional): Whether to log to console. Defaults to True.
        format_str (str, optional): Log message format. Defaults to DEFAULT_LOG_FORMAT.
        date_format (str, optional): Date format for log entries. Defaults to DEFAULT_DATE_FORMAT.
        max_bytes (int, optional): Maximum bytes per log file. Defaults to 10MB.
        backup_count (int, optional): Number of backup log files. Defaults to 5.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set log level
    logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set default formats if not provided
    if format_str is None:
        format_str = DEFAULT_LOG_FORMAT
    if date_format is None:
        date_format = DEFAULT_DATE_FORMAT
    
    # Create formatter
    formatter = logging.Formatter(format_str, date_format)
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def setup_app_logger(
    config,
    console: bool = True,
    level: str = "info"
) -> logging.Logger:
    """Set up the main application logger using the application configuration.
    
    Args:
        config: Configuration object with logging settings.
        console (bool, optional): Whether to log to console. Defaults to True.
        level (str, optional): Override log level. Defaults to "info".
        
    Returns:
        logging.Logger: Configured application logger.
    """
    # Get log file path from config
    log_dir = getattr(config, "LOG_DIR", "logs")
    
    # Create main log file path
    log_file = os.path.join(log_dir, "diagnostic_system.log")
    
    # Get log level
    config_level = getattr(config, "LOG_LEVEL", level).lower()
    
    # Set up logger
    return setup_logger(
        name="diagnostic_system",
        log_file=log_file,
        level=config_level,
        console=console,
        max_bytes=getattr(config, "LOG_MAX_BYTES", 10485760),
        backup_count=getattr(config, "LOG_BACKUP_COUNT", 5)
    )


def setup_component_logger(
    component_name: str,
    config,
    console: bool = False,
    level: Optional[str] = None
) -> logging.Logger:
    """Set up a logger for a specific application component.
    
    Args:
        component_name (str): Name of the component (e.g., "storage", "ui").
        config: Configuration object with logging settings.
        console (bool, optional): Whether to log to console. Defaults to False.
        level (str, optional): Override log level. If None, uses app default.
        
    Returns:
        logging.Logger: Configured component logger.
    """
    # Get log file path from config
    log_dir = getattr(config, "LOG_DIR", "logs")
    
    # Create component log file path
    component_log_file = os.path.join(log_dir, f"{component_name}.log")
    
    # Get log level
    if level is None:
        level = getattr(config, "LOG_LEVEL", "info").lower()
    
    # Full logger name
    logger_name = f"diagnostic_system.{component_name}"
    
    # Set up logger
    return setup_logger(
        name=logger_name,
        log_file=component_log_file,
        level=level,
        console=console,
        max_bytes=getattr(config, "LOG_MAX_BYTES", 10485760),
        backup_count=getattr(config, "LOG_BACKUP_COUNT", 5)
    )


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An exception occurred",
    level: str = "error"
) -> None:
    """Log an exception with traceback.
    
    Args:
        logger (logging.Logger): Logger to use.
        exception (Exception): Exception to log.
        message (str, optional): Message to include. Defaults to "An exception occurred".
        level (str, optional): Log level. Defaults to "error".
    """
    # Get traceback as string
    tb_str = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )
    
    # Build log message
    log_message = f"{message}: {str(exception)}\n{''.join(tb_str)}"
    
    # Log at specified level
    log_function = getattr(logger, level.lower(), logger.error)
    log_function(log_message)


def log_method_call(
    logger: logging.Logger,
    method_name: str,
    args: Tuple = None,
    kwargs: Dict[str, Any] = None,
    level: str = "debug"
) -> None:
    """Log a method call with arguments.
    
    Args:
        logger (logging.Logger): Logger to use.
        method_name (str): Name of the method being called.
        args (tuple, optional): Positional arguments. Defaults to None.
        kwargs (dict, optional): Keyword arguments. Defaults to None.
        level (str, optional): Log level. Defaults to "debug".
    """
    # Format arguments
    args_str = str(args) if args else "()"
    kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    
    # Build log message
    if kwargs_str:
        log_message = f"Calling {method_name}{args_str} with {kwargs_str}"
    else:
        log_message = f"Calling {method_name}{args_str}"
    
    # Log at specified level
    log_function = getattr(logger, level.lower(), logger.debug)
    log_function(log_message)


def log_method_result(
    logger: logging.Logger,
    method_name: str,
    result: Any,
    level: str = "debug"
) -> None:
    """Log the result of a method call.
    
    Args:
        logger (logging.Logger): Logger to use.
        method_name (str): Name of the method.
        result (Any): Result to log.
        level (str, optional): Log level. Defaults to "debug".
    """
    # Build log message
    log_message = f"{method_name} returned: {result}"
    
    # Log at specified level
    log_function = getattr(logger, level.lower(), logger.debug)
    log_function(log_message)


def capture_log_to_string(
    name: str,
    level: str = "info",
    format_str: Optional[str] = None
) -> Tuple[logging.Logger, logging.StreamHandler]:
    """Capture log output to a string for testing or reporting.
    
    Args:
        name (str): Logger name.
        level (str, optional): Log level. Defaults to "info".
        format_str (str, optional): Log format string. Defaults to DEFAULT_LOG_FORMAT.
        
    Returns:
        tuple: (Logger, StringHandler) - Use handler.getvalue() to get log content.
    """
    import io
    
    # Set default format if not provided
    if format_str is None:
        format_str = DEFAULT_LOG_FORMAT
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create string IO handler
    string_io = io.StringIO()
    string_handler = logging.StreamHandler(string_io)
    string_handler.setFormatter(logging.Formatter(format_str))
    
    # Add custom getvalue method
    def getvalue():
        return string_io.getvalue()
    string_handler.getvalue = getvalue
    
    logger.addHandler(string_handler)
    
    return logger, string_handler


def create_log_filter(excluded_modules: List[str] = None, min_level: str = "info") -> logging.Filter:
    """Create a filter to exclude specific modules or log levels.
    
    Args:
        excluded_modules (list, optional): List of module names to exclude.
        min_level (str, optional): Minimum log level to include. Defaults to "info".
        
    Returns:
        logging.Filter: Filter to attach to a handler.
    """
    class CustomFilter(logging.Filter):
        def filter(self, record):
            # Filter by module
            if excluded_modules:
                for module in excluded_modules:
                    if record.name.startswith(module):
                        return False
            
            # Filter by level
            if LOG_LEVELS.get(min_level.lower(), logging.INFO) > record.levelno:
                return False
                
            return True
    
    return CustomFilter()


def configure_root_logger(
    level: str = "warning",
    console: bool = True
) -> None:
    """Configure the root logger for basic logging.
    
    Args:
        level (str, optional): Log level. Defaults to "warning".
        console (bool, optional): Whether to log to console. Defaults to True.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set level
    root_logger.setLevel(LOG_LEVELS.get(level.lower(), logging.WARNING))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        root_logger.addHandler(console_handler)


def disable_external_loggers(modules: List[str] = None) -> None:
    """Disable or reduce log level for external modules.
    
    Args:
        modules (list, optional): List of modules to disable. 
                                Defaults to ['urllib3', 'matplotlib', 'PIL'].
    """
    if modules is None:
        modules = ['urllib3', 'matplotlib', 'PIL']
        
    for module in modules:
        logging.getLogger(module).setLevel(logging.WARNING)


def log_function_timer(
    logger: logging.Logger,
    level: str = "debug"
) -> callable:
    """Decorator to log function execution time.
    
    Args:
        logger (logging.Logger): Logger to use.
        level (str, optional): Log level. Defaults to "debug".
        
    Returns:
        callable: Decorator function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Record start time
            start_time = datetime.now()
            
            # Call function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            # Log execution time
            log_function = getattr(logger, level.lower(), logger.debug)
            log_function(f"{func.__name__} executed in {execution_time.total_seconds():.4f} seconds")
            
            return result
        return wrapper
    return decorator


def log_to_file(
    message: str,
    log_file: str,
    level: str = "info",
    timestamp: bool = True,
    append: bool = True
) -> bool:
    """Directly log a message to a file without setting up a logger.
    
    Args:
        message (str): Message to log.
        log_file (str): Path to log file.
        level (str, optional): Log level. Defaults to "info".
        timestamp (bool, optional): Whether to add a timestamp. Defaults to True.
        append (bool, optional): Whether to append or overwrite. Defaults to True.
        
    Returns:
        bool: Success flag.
    """
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        # Format message
        if timestamp:
            timestamp_str = datetime.now().strftime(DEFAULT_DATE_FORMAT)
            formatted_message = f"{timestamp_str} - {level.upper()} - {message}\n"
        else:
            formatted_message = f"{message}\n"
        
        # Write to file
        mode = "a" if append else "w"
        with open(log_file, mode, encoding="utf-8") as f:
            f.write(formatted_message)
            
        return True
    except Exception as e:
        # Print error to stderr since we can't use logging
        print(f"Error writing to log file {log_file}: {str(e)}", file=sys.stderr)
        return False


def get_log_dir(config) -> str:
    """Get the log directory from config, creating it if needed.
    
    Args:
        config: Configuration object with logging settings.
        
    Returns:
        str: Path to the log directory.
    """
    log_dir = getattr(config, "LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_all_log_files(config) -> List[str]:
    """Get a list of all log files.
    
    Args:
        config: Configuration object with logging settings.
        
    Returns:
        list: List of log file paths.
    """
    log_dir = get_log_dir(config)
    
    # Get all .log files
    log_files = []
    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):
            log_files.append(os.path.join(log_dir, filename))
            
    return log_files


def clear_log_file(log_file: str, backup: bool = True) -> bool:
    """Clear a log file, optionally creating a backup.
    
    Args:
        log_file (str): Path to log file.
        backup (bool, optional): Whether to create a backup. Defaults to True.
        
    Returns:
        bool: Success flag.
    """
    try:
        if not os.path.exists(log_file):
            return True
            
        # Create backup if requested
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{log_file}.{timestamp}.bak"
            import shutil
            shutil.copy2(log_file, backup_file)
        
        # Clear the file
        with open(log_file, "w") as f:
            pass
            
        return True
    except Exception as e:
        print(f"Error clearing log file {log_file}: {str(e)}", file=sys.stderr)
        return False


def rotate_log_file(log_file: str, max_bytes: int = 10485760, backup_count: int = 5) -> bool:
    """Manually rotate a log file if it exceeds max_bytes.
    
    Args:
        log_file (str): Path to log file.
        max_bytes (int, optional): Maximum file size in bytes. Defaults to 10MB.
        backup_count (int, optional): Number of backup files. Defaults to 5.
        
    Returns:
        bool: True if rotated, False otherwise.
    """
    try:
        if not os.path.exists(log_file):
            return False
            
        # Check file size
        if os.path.getsize(log_file) <= max_bytes:
            return False
            
        # Perform rotation
        if backup_count > 0:
            # Shift existing backups
            for i in range(backup_count - 1, 0, -1):
                src = f"{log_file}.{i}"
                dst = f"{log_file}.{i+1}"
                
                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)
            
            # Rotate current log file
            dst = f"{log_file}.1"
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(log_file, dst)
            
            # Create new empty log file
            with open(log_file, "w") as f:
                pass
        else:
            # Just clear the file
            with open(log_file, "w") as f:
                pass
                
        return True
    except Exception as e:
        print(f"Error rotating log file {log_file}: {str(e)}", file=sys.stderr)
        return False


def set_log_level(
    logger: logging.Logger,
    level: str
) -> None:
    """Set the log level for a logger and all its handlers.
    
    Args:
        logger (logging.Logger): Logger to modify.
        level (str): New log level ("debug", "info", "warning", "error", "critical").
    """
    # Set logger level
    logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
    
    # Set level for all handlers
    for handler in logger.handlers:
        handler.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))


def create_custom_logger(
    name: str,
    console_level: str = "info",
    file_level: str = "debug",
    file_path: Optional[str] = None
) -> logging.Logger:
    """Create a logger with different levels for console and file handlers.
    
    Args:
        name (str): Logger name.
        console_level (str, optional): Console log level. Defaults to "info".
        file_level (str, optional): File log level. Defaults to "debug".
        file_path (str, optional): Log file path. If None, uses name.log.
        
    Returns:
        logging.Logger: Configured logger.
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set logger level to the most verbose of the two levels
    console_level_num = LOG_LEVELS.get(console_level.lower(), logging.INFO)
    file_level_num = LOG_LEVELS.get(file_level.lower(), logging.DEBUG)
    logger.setLevel(min(console_level_num, file_level_num))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level_num)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if file_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=10485760, backupCount=5
        )
        file_handler.setLevel(file_level_num)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class StructuredLogger:
    """A logger that produces structured log entries as JSON objects."""
    
    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        console: bool = True,
        level: str = "info"
    ):
        """Initialize structured logger.
        
        Args:
            name (str): Logger name.
            log_file (str, optional): Log file path. Defaults to None.
            console (bool, optional): Whether to log to console. Defaults to True.
            level (str, optional): Log level. Defaults to "info".
        """
        import json
        self.json = json
        
        # Create base logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter for structured logging
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                # Base log entry
                log_entry = {
                    "timestamp": self.formatTime(record, DEFAULT_DATE_FORMAT),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage()
                }
                
                # Add extra attributes
                for key, value in record.__dict__.items():
                    if key not in ["args", "exc_info", "exc_text", "msg", "created", 
                                 "msecs", "relativeCreated", "levelname", "name"]:
                        log_entry[key] = value
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": "".join(traceback.format_exception(*record.exc_info))
                    }
                
                return json.dumps(log_entry)
        
        formatter = StructuredFormatter()
        
        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if requested
        if log_file:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10485760, backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with structured data.
        
        Args:
            level (str): Log level.
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        # Get log function
        log_function = getattr(self.logger, level.lower(), self.logger.info)
        
        # Add extra fields to log record
        extra = kwargs
        
        # Log with extra fields
        log_function(message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        self.log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        self.log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        self.log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        self.log("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message (str): Log message.
            **kwargs: Additional fields to include in the log entry.
        """
        self.log("critical", message, **kwargs)
    
    def exception(self, message: str, exc_info=True, **kwargs) -> None:
        """Log an exception.
        
        Args:
            message (str): Log message.
            exc_info (bool, optional): Whether to include exception info. Defaults to True.
            **kwargs: Additional fields to include in the log entry.
        """
        self.logger.exception(message, extra=kwargs)


# Audit logger for tracking user actions and system changes
class AuditLogger:
    """Logger for tracking user actions and system changes."""
    
    def __init__(
        self,
        config,
        component: str = "system"
    ):
        """Initialize the audit logger.
        
        Args:
            config: Configuration object with logging settings.
            component (str, optional): Component name. Defaults to "system".
        """
        # Get log directory
        log_dir = getattr(config, "LOG_DIR", "logs")
        audit_log_file = os.path.join(log_dir, f"audit_{component}.log")
        
        # Set up structured logger
        self.logger = StructuredLogger(
            name=f"audit.{component}",
            log_file=audit_log_file,
            console=False,
            level="info"
        )
        
        self.component = component
    
    def log_action(
        self,
        action: str,
        user: str = "system",
        details: Dict[str, Any] = None,
        status: str = "success",
        target: str = None
    ) -> None:
        """Log a user or system action.
        
        Args:
            action (str): Action being performed.
            user (str, optional): User performing the action. Defaults to "system".
            details (dict, optional): Additional details about the action.
            status (str, optional): Action status. Defaults to "success".
            target (str, optional): Target of the action. Defaults to None.
        """
        # Build message
        message = f"Action: {action}"
        if target:
            message += f" on {target}"
        
        # Log with structured data
        self.logger.info(
            message,
            action=action,
            user=user,
            component=self.component,
            status=status,
            target=target,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def log_rule_change(
        self,
        rule_id: str,
        change_type: str,
        user: str = "system",
        details: Dict[str, Any] = None
    ) -> None:
        """Log a rule change.
        
        Args:
            rule_id (str): ID of the rule.
            change_type (str): Type of change ("create", "update", "delete", "apply").
            user (str, optional): User making the change. Defaults to "system".
            details (dict, optional): Additional details about the change.
        """
        self.log_action(
            action=change_type,
            user=user,
            target=f"rule:{rule_id}",
            details=details
        )
    
    def log_system_event(
        self,
        event: str,
        details: Dict[str, Any] = None,
        status: str = "success"
    ) -> None:
        """Log a system event.
        
        Args:
            event (str): Event description.
            details (dict, optional): Additional details about the event.
            status (str, optional): Event status. Defaults to "success".
        """
        self.log_action(
            action="system_event",
            user="system",
            details={"event": event, **(details or {})},
            status=status
        )