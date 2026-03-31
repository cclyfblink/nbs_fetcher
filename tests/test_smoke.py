import nbs_fetcher


def test_import() -> None:
    assert nbs_fetcher is not None


def test_version_present() -> None:
    assert isinstance(nbs_fetcher.__version__, str)


def test_list_pages() -> None:
    pages = nbs_fetcher.list_pages()
    assert pages
    assert any(page["name"] == "fsMonthData" for page in pages)
    assert any(page["code"] == 4 for page in pages)


def test_primary_pages_have_root_metadata() -> None:
    pages = nbs_fetcher.list_pages()
    fs_page = next(page for page in pages if page["name"] == "fsMonthData")
    assert fs_page["root_name"] == "分省月度数据"
    assert fs_page["root_id"]


def test_tree_query() -> None:
    nodes = nbs_fetcher.tree("fsMonthData", path="能源")
    assert nodes
    assert any(node["name"] == "能源主要产品产量" for node in nodes)


def test_indicators_query() -> None:
    items = nbs_fetcher.indicators("fsMonthData", path="能源/能源主要产品产量/发电量")
    assert items
    assert any(item["series_type"] == "current_value" for item in items)
    assert any(item["series_type"] == "cumulative_value" for item in items)


def test_areas_query_supports_code6_metadata() -> None:
    items = nbs_fetcher.areas("fsMonthData", path="能源/能源主要产品产量/发电量", series="current_value")
    assert items
    beijing = next(item for item in items if item["text"] == "北京市")
    assert beijing["code6"] == "110000"


def test_fetch_records_output_shape() -> None:
    result = nbs_fetcher.fetch(
        "fsMonthData",
        path="能源/能源主要产品产量/发电量",
        series="current_value",
        areas="110000",
        dts="202401-202412",
        sequence="area",
        format="records",
    )
    assert result["page"] == "fsMonthData"
    assert result["sequence"] == "area"
    assert result["row_count"] > 0
    assert result["records"]
    assert result["records"][0]["area_code6"] == "110000"


def test_fetch_matrix_output_shape() -> None:
    result = nbs_fetcher.fetch(
        "fsMonthData",
        path="能源/能源主要产品产量/发电量",
        series=["current_value", "cumulative_value"],
        areas="110000",
        dts="202401-202412",
        sequence="area",
        format="matrix",
    )
    assert result["page"] == "fsMonthData"
    assert result["row_count"] == 2
    assert result["matrix"]
    assert any(row["series_type"] == "current_value" for row in result["matrix"])
    assert any(row["series_type"] == "cumulative_value" for row in result["matrix"])
