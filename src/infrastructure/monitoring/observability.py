import time
import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger("flight_scraper")

class ObservabilityManager:
    def __init__(self, metrics_filepath: Optional[str] = "metrics.json"):
        self.metrics_filepath = metrics_filepath
        self.start_time = 0.0
        self.end_time = 0.0
        self.stats = {
            "total_queries": 0,
            "successes": 0,
            "failures": 0,
            "no_flights": 0,
            "anti_bot_blocks": 0,
            "latencies": []
        }

    def start_session(self) -> None:
        self.start_time = time.time()
        logger.info("Observability monitoring session started.")

    def record_query(self, status: str, duration: float, anti_bot_hit: bool = False) -> None:
        self.stats["total_queries"] += 1
        self.stats["latencies"].append(duration)
        
        if anti_bot_hit:
            self.stats["anti_bot_blocks"] += 1
            
        if status == "Success":
            self.stats["successes"] += 1
        elif status == "No Flights":
            self.stats["no_flights"] += 1
        else:
            self.stats["failures"] += 1

    async def end_session(self) -> Dict[str, Any]:
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Calculate latency statistics
        latencies = self.stats["latencies"]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        min_latency = min(latencies) if latencies else 0.0
        
        metrics_summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration_seconds": round(total_duration, 2),
            "total_queries": self.stats["total_queries"],
            "success_rate_percent": round((self.stats["successes"] / self.stats["total_queries"] * 100), 2) if self.stats["total_queries"] else 0.0,
            "successes": self.stats["successes"],
            "failures": self.stats["failures"],
            "no_flights": self.stats["no_flights"],
            "anti_bot_blocks": self.stats["anti_bot_blocks"],
            "latency": {
                "average_seconds": round(avg_latency, 2),
                "max_seconds": round(max_latency, 2),
                "min_seconds": round(min_latency, 2)
            }
        }
        
        # Log structured JSON metric representation (great for Loki/Logstash)
        logger.info(f"Structured Metrics: {json.dumps(metrics_summary)}")
        
        if self.metrics_filepath:
            await self.save_metrics_file(metrics_summary)
            
        return metrics_summary

    async def save_metrics_file(self, summary: Dict[str, Any]) -> None:
        try:
            import aiofiles
            
            filepath = os.path.abspath(self.metrics_filepath)
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
                
            # If metrics file already exists, let's append to a history array
            history = []
            if os.path.exists(filepath):
                try:
                    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                        content = await f.read()
                        old_data = json.loads(content)
                        if isinstance(old_data, list):
                            history = old_data
                        else:
                            history = [old_data]
                except Exception:
                    pass
                    
            history.append(summary)
            
            # Keep only the last 50 execution records to prevent unbounded size
            if len(history) > 50:
                history = history[-50:]
                
            data_str = await asyncio.to_thread(json.dumps, history, indent=4)
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(data_str)
                
            logger.info(f"Observability metrics successfully saved asynchronously to: {filepath}")
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to write metrics report: {e}")
