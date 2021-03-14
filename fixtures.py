def mock_album(id="", genres=[], artists=[], name=[]):
    return dict(
        album_type="",
        artists=artists,
        available_markets=[],
        copyrights=[],
        external_ids=[],
        external_urls=[],
        genres=genres,
        href="",
        id=id,
        images="",
        label="",
        name=name,
        popularity=0,
        release_date="",
        release_date_precision=1,
        total_tracks=0,
        tracks=[],
        type="",
        uri=""
    )

def mock_track():
    return dict(uri="")

def mock_artist():
    return dict(id="123")