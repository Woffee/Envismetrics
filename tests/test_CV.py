import pytest
import os
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from src.CV import CV, Search_scan_rate


def test_search_scan_rate_valid():
    assert Search_scan_rate("DMAB_10mVs.csv") == 10
    assert Search_scan_rate("sample_500mVs.txt") == 500

def test_search_scan_rate_invalid():
    assert Search_scan_rate("file_without_scanrate.csv") == -1


@patch.object(CV, 'read_data')
def test_start1_success(mock_read_data, tmp_path):
    df = pd.DataFrame({
        "WE(1).Current (A)": [0.1, 0.2, 0.3],
        "WE(1).Potential (V)": [-0.1, 0.0, 0.1],
        "Scan": [1, 1, 1]
    })

    mock_read_data.return_value = {10: df}

    # Save dummy files_info
    info_file = tmp_path / "files_info.json"
    info_file.write_text(json.dumps([{
        "filename": "data_10mVs.xlsx",
        "existed_filename": "dummy_path.xlsx"
    }]))

    cv = CV(version="v_test", files_info=str(info_file))
    cv.datapath = tmp_path
    cv.savepath = tmp_path

    result = cv.start1({"sigma": "1.0", "cycle": "1"})
    assert result["status"] is True
    out = result["data"]["CV"]["form1"]["output"]
    assert os.path.exists(tmp_path / out["file1"])
    assert os.path.exists(tmp_path / out["file2"])
    assert os.path.exists(tmp_path / out["file3"])