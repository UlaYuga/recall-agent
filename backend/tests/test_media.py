from app.api.media import public_media_url


def test_public_media_url_keeps_external_url() -> None:
    assert (
        public_media_url("https://cdn.example.com/video.mp4", storage_dir="./storage")
        == "https://cdn.example.com/video.mp4"
    )


def test_public_media_url_keeps_existing_storage_url() -> None:
    assert (
        public_media_url("/storage/cmp/video.mp4", storage_dir="./storage")
        == "/storage/cmp/video.mp4"
    )


def test_public_media_url_converts_local_storage_path(tmp_path) -> None:
    storage_dir = tmp_path / "storage"
    media_path = storage_dir / "cmp_1" / "video.mp4"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"mp4")

    assert (
        public_media_url(str(media_path), storage_dir=str(storage_dir))
        == "/storage/cmp_1/video.mp4"
    )


def test_public_media_url_keeps_path_outside_storage(tmp_path) -> None:
    storage_dir = tmp_path / "storage"
    outside = tmp_path / "other" / "video.mp4"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"mp4")

    assert public_media_url(str(outside), storage_dir=str(storage_dir)) == str(outside)


def test_public_media_url_accepts_none() -> None:
    assert public_media_url(None, storage_dir="./storage") is None
