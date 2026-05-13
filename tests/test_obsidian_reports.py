from polybot.obsidian.reports import render_collection_report


def test_render_collection_report_links_data_layer() -> None:
    note = render_collection_report(
        title="Daily Collection",
        source="test",
        rows_seen=2,
        rows_written=2,
    )

    assert "# Daily Collection" in note
    assert "[[Data Layer]]" in note

