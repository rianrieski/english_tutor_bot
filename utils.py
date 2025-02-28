import functools
import asyncio
from telegram.error import TimedOut
import httpx
from openai import APIError
from logger_config import setup_logger

logger = setup_logger('utils', 'utils.log')

def retry_on_timeout(max_retries=3, initial_delay=1):
    """Decorator to retry functions on timeout with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (TimedOut, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Final retry attempt failed: {str(e)}")
                        raise
                    
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (httpx.ConnectTimeout, httpx.ReadTimeout, APIError) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Final retry attempt failed: {str(e)}")
                        raise
                    
                    wait_time = delay * (2 ** attempt)
                    logger.info(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    asyncio.sleep(wait_time)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 