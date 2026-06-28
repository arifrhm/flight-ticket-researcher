import os
import json
import pytest
import logging
from src.infrastructure.monitoring.logger import setup_logger
from src.infrastructure.monitoring.observability import ObservabilityManager

def test_logger_setup(tmp_path):
    log_file = os.path.join(tmp_path, "nested_log_dir/scraper.log")
    logger = setup_logger(log_file=log_file)
    
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 2
    assert os.path.exists(log_file) is True

@pytest.mark.asyncio
async def test_observability_manager(tmp_path):
    # Use nested path to trigger directory creation branch (not exists)
    metrics_file = os.path.join(tmp_path, "nested_metrics_dir/metrics.json")
    
    # 1. Non-list check: Pre-create metrics file with a single dict
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    with open(metrics_file, "w") as f:
        json.dump({"dummy": "value"}, f)
        
    obs = ObservabilityManager(metrics_filepath=metrics_file)
    obs.start_session()
    obs.record_query(status="Success", duration=1.5, anti_bot_hit=False)
    summary = await obs.end_session()
    
    # Verify non-list was converted to a list of length 2
    with open(metrics_file, "r") as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0] == {"dummy": "value"}
    assert data[1]["total_queries"] == 1
    
    # 2. List check: Run another session to verify it appends to existing list
    obs2 = ObservabilityManager(metrics_filepath=metrics_file)
    obs2.start_session()
    obs2.record_query(status="No Flights", duration=0.8, anti_bot_hit=True)
    obs2.record_query(status="Failed", duration=2.2, anti_bot_hit=False)
    summary2 = await obs2.end_session()
    
    with open(metrics_file, "r") as f:
        data2 = json.load(f)
    assert len(data2) == 3
    assert data2[2]["total_queries"] == 2
    
    # 3. Truncation check: Pre-populate history with 55 dummy entries
    dummy_history = [{"id": i} for i in range(55)]
    with open(metrics_file, "w") as f:
        json.dump(dummy_history, f)
        
    obs3 = ObservabilityManager(metrics_filepath=metrics_file)
    obs3.start_session()
    obs3.record_query(status="Success", duration=0.5)
    await obs3.end_session()
    
    with open(metrics_file, "r") as f:
        truncated_data = json.load(f)
    assert len(truncated_data) == 50
    assert truncated_data[-1]["total_queries"] == 1

@pytest.mark.asyncio
async def test_observability_invalid_json(tmp_path):
    metrics_file = os.path.join(tmp_path, "metrics_dir/metrics.json")
    
    # Pre-create parent directory and fill the metrics file with invalid JSON to trigger parse exception (lines 96-97)
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    with open(metrics_file, "w") as f:
        f.write("invalid json string content")
        
    obs = ObservabilityManager(metrics_filepath=metrics_file)
    obs.start_session()
    obs.record_query(status="Success", duration=1.0)
    await obs.end_session()
    
    # Assert it recovered from the json decode error and successfully wrote the new entry
    assert os.path.exists(metrics_file) is True
    with open(metrics_file, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["total_queries"] == 1

@pytest.mark.asyncio
async def test_observability_directory_creation(tmp_path):
    # Path where directory does not exist to trigger makedirs (line 83)
    metrics_file = os.path.join(tmp_path, "fresh_metrics_dir/sub_dir/metrics.json")
    
    obs = ObservabilityManager(metrics_filepath=metrics_file)
    obs.start_session()
    obs.record_query(status="Success", duration=1.0)
    await obs.end_session()
    
    # Assert directory was created and file written
    assert os.path.exists(metrics_file) is True
