from unittest.mock import patch, MagicMock
from src.main import run_pipeline, check_already_sent_today

@patch("src.main.fetch_all_categories")
@patch("src.main.generate_morning_digest")
@patch("src.main.save_web_artifacts")
@patch("src.main.send_email")
def test_run_pipeline_dry_run(mock_send, mock_save, mock_digest, mock_fetch):
    mock_fetch.return_value = {"finance_markets": []}
    mock_digest.return_value = MagicMock(headline_quote="测试", date_str="2026-11-03")
    
    code = run_pipeline(dry_run=True, no_email=False, test_sources=False)
    assert code == 0
    mock_fetch.assert_called_once()
    mock_digest.assert_called_once()
    mock_save.assert_called_once()
    mock_send.assert_not_called()

@patch("src.main.check_already_sent_today")
@patch("src.main.fetch_all_categories")
def test_run_pipeline_skip_duplicate(mock_fetch, mock_check):
    mock_check.return_value = True
    
    # 已经被标记为今天已发送，且未传 force=True 时，应该直接跳过并返回 0
    code = run_pipeline(dry_run=False, no_email=False, test_sources=False, force=False)
    assert code == 0
    mock_fetch.assert_not_called()
