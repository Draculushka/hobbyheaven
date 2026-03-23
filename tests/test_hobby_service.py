import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile, HTTPException

from models import User, Persona, Hobby, Tag
from services.hobby_service import (
    sanitize_description,
    save_upload_image,
    search_hobbies,
    process_tags,
    create_hobby,
    delete_hobby,
)


# ─── helpers ────────────────────────────────────────────────────────────────

JPEG_MAGIC = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # valid JPEG header

def make_upload_file(filename="test.jpg", content=None, size=None):
    if content is None:
        content = JPEG_MAGIC
    if size is not None:
        content = JPEG_MAGIC + b'\x00' * (size - len(JPEG_MAGIC))
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.file = io.BytesIO(content)
    return file


def _make_user(db, email="u@test.com", deleted_at=None):
    u = User(email=email, hashed_password="x", is_active=True, deleted_at=deleted_at)
    db.add(u)
    db.flush()
    return u


def _make_persona(db, user, username="persona1"):
    p = Persona(user_id=user.id, username=username)
    db.add(p)
    db.flush()
    return p


def _make_hobby(db, persona, title="Hobby", description="desc"):
    h = Hobby(persona_id=persona.id, title=title, description=description,
              created_at=datetime.now(timezone.utc))
    db.add(h)
    db.flush()
    return h


# ═══════════════════════════════════════════════════════════════════════════
#  sanitize_description
# ═══════════════════════════════════════════════════════════════════════════

class TestSanitizeDescription:
    # TP-HS01
    def test_plain_text_unchanged(self):
        assert sanitize_description("Hello world") == "Hello world"

    # TP-HS02
    def test_allowed_tags_preserved(self):
        html = '<b>bold</b> <i>italic</i> <a href="https://example.com">link</a>'
        result = sanitize_description(html)
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result
        assert '<a href="https://example.com"' in result
        assert "link</a>" in result

    # TP-HS03
    def test_forbidden_tags_stripped(self):
        result = sanitize_description('<script>alert(1)</script><iframe src="x"></iframe>OK')
        assert "<script>" not in result
        assert "<iframe" not in result
        assert "OK" in result

    # TP-HS04 (P0)
    def test_javascript_protocol_removed(self):
        result = sanitize_description('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

    # TP-HS05
    def test_img_onerror_removed(self):
        result = sanitize_description('<img onerror="alert(1)">')
        assert "onerror" not in result

    # TP-HS06
    def test_empty_string(self):
        assert sanitize_description("") == ""


# ═══════════════════════════════════════════════════════════════════════════
#  save_upload_image
# ═══════════════════════════════════════════════════════════════════════════

class TestSaveUploadImage:
    # TP-HS07
    def test_none_returns_none(self):
        assert save_upload_image(None) is None

    # TP-HS08
    @patch("services.hobby_service.upload_file_to_s3")
    def test_valid_jpg(self, mock_upload):
        mock_upload.return_value = "http://s3/photo.jpg"
        f = make_upload_file("photo.jpg")
        f.content_type = "image/jpeg"
        result = save_upload_image(f)
        assert result == "http://s3/photo.jpg"
        assert mock_upload.called

    # TP-HS09 (P0)
    def test_exe_rejected(self):
        f = make_upload_file("malware.exe")
        with pytest.raises(HTTPException) as exc_info:
            save_upload_image(f)
        assert exc_info.value.status_code == 400

    # TP-HS10
    @patch("services.hobby_service.upload_file_to_s3")
    def test_exactly_5mb_accepted(self, mock_upload):
        mock_upload.return_value = "http://s3/img.jpg"
        f = make_upload_file("img.jpg", size=5 * 1024 * 1024)
        f.content_type = "image/jpeg"
        result = save_upload_image(f)
        assert result == "http://s3/img.jpg"

    # TP-HS11
    def test_over_5mb_rejected(self):
        f = make_upload_file("img.jpg", size=5 * 1024 * 1024 + 1)
        with pytest.raises(HTTPException) as exc_info:
            save_upload_image(f)
        assert exc_info.value.status_code == 400

    # TP-HS12
    @patch("services.hobby_service.upload_file_to_s3")
    def test_uppercase_extension_accepted(self, mock_upload):
        mock_upload.return_value = "http://s3/photo.jpg"
        f = make_upload_file("photo.JPG")
        f.content_type = "image/jpeg"
        result = save_upload_image(f)
        assert result == "http://s3/photo.jpg"

    # TP-HS13
    @patch("services.hobby_service.upload_file_to_s3")
    def test_path_traversal_replaced_by_uuid(self, mock_upload):
        mock_upload.return_value = "http://s3/replaced.jpg"
        f = make_upload_file("../../../etc/passwd.jpg")
        f.content_type = "image/jpeg"
        result = save_upload_image(f)
        assert result == "http://s3/replaced.jpg"


# ═══════════════════════════════════════════════════════════════════════════
#  search_hobbies
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchHobbies:
    # TP-HS14
    def test_empty_search_returns_all(self, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        _make_hobby(db, p, title="Painting")
        _make_hobby(db, p, title="Cooking")
        db.commit()
        hobbies, _ = search_hobbies(db, "", cursor=None, limit=10)
        assert len(hobbies) == 2

    # TP-HS15
    def test_synonym_matching(self, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        _make_hobby(db, p, title="шахматы – мой мир")
        _make_hobby(db, p, title="Chess club")
        _make_hobby(db, p, title="Painting")
        db.commit()
        hobbies, _ = search_hobbies(db, "chess", cursor=None, limit=10)
        assert len(hobbies) == 2

    # TP-HS16 (P0)
    def test_like_percent_escaped(self, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        _make_hobby(db, p, title="100% fun")
        _make_hobby(db, p, title="Painting")
        db.commit()
        hobbies, _ = search_hobbies(db, "%", cursor=None, limit=10)
        # "%" should be escaped; only hobby with literal % should match
        titles = [h.title for h in hobbies]
        assert "100% fun" in titles
        assert "Painting" not in titles

    # TP-HS17 (P0)
    def test_like_underscore_escaped(self, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        _make_hobby(db, p, title="my_hobby")
        _make_hobby(db, p, title="Painting")
        db.commit()
        hobbies, _ = search_hobbies(db, "_", cursor=None, limit=10)
        titles = [h.title for h in hobbies]
        assert "my_hobby" in titles
        assert "Painting" not in titles

    # TP-HS18
    def test_empty_results_next_cursor_none(self, db):
        u = _make_user(db)
        _make_persona(db, u)
        db.commit()
        hobbies, next_cursor = search_hobbies(db, "", cursor=None, limit=10)
        assert hobbies == []
        assert next_cursor is None

    # TP-HS19
    def test_pagination_with_cursor(self, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        hobbies_created = []
        for i in range(11):
            h = _make_hobby(db, p, title=f"Hobby {i}")
            hobbies_created.append(h)
        db.commit()

        # First page
        hobbies, next_cursor = search_hobbies(db, "", cursor=None, limit=10)
        assert len(hobbies) == 10
        assert next_cursor is not None

        # Second page
        hobbies2, next_cursor2 = search_hobbies(db, "", cursor=next_cursor, limit=10)
        assert len(hobbies2) == 1
        assert next_cursor2 is None

    # TP-HS20
    def test_soft_deleted_user_excluded(self, db):
        active_user = _make_user(db, email="active@test.com")
        deleted_user = _make_user(db, email="deleted@test.com",
                                  deleted_at=datetime.now(timezone.utc))
        p1 = _make_persona(db, active_user, username="active_p")
        p2 = _make_persona(db, deleted_user, username="deleted_p")
        _make_hobby(db, p1, title="Active Hobby")
        _make_hobby(db, p2, title="Deleted Hobby")
        db.commit()
        hobbies, _ = search_hobbies(db, "", cursor=None, limit=10)
        titles = [h.title for h in hobbies]
        assert "Active Hobby" in titles
        assert "Deleted Hobby" not in titles



# ═══════════════════════════════════════════════════════════════════════════
#  process_tags
# ═══════════════════════════════════════════════════════════════════════════

class TestProcessTags:
    # TP-HS26
    def test_empty_string(self, db):
        assert process_tags(db, "") == []

    # TP-HS27
    def test_two_tags_created(self, db):
        tags = process_tags(db, "tag1, tag2")
        assert len(tags) == 2
        assert tags[0].name == "tag1"
        assert tags[1].name == "tag2"

    # TP-HS28
    def test_existing_tag_not_duplicated(self, db):
        existing = Tag(name="tag1")
        db.add(existing)
        db.flush()
        tags = process_tags(db, "tag1, tag2")
        assert len(tags) == 2
        assert tags[0].id == existing.id  # same row

    # TP-HS29
    def test_whitespace_only_items_filtered(self, db):
        tags = process_tags(db, "  ,  , ")
        assert tags == []

    # BUG-3: duplicates deduplicated
    def test_duplicate_tags_deduplicated(self, db):
        tags = process_tags(db, "tag1, tag1")
        assert len(tags) == 1
        assert tags[0].name == "tag1"


# ═══════════════════════════════════════════════════════════════════════════
#  create_hobby / delete_hobby
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateDeleteHobby:
    # TP-HS21
    @patch("services.hobby_service.save_upload_image", return_value=None)
    def test_create_hobby_sanitizes_description(self, _mock_img, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        db.commit()
        hobby = create_hobby(db, p.id, "Title", "<script>alert(1)</script>Safe", "", None)
        assert "<script>" not in hobby.description
        assert "Safe" in hobby.description

    # TP-HS22
    @patch("services.hobby_service.save_upload_image", return_value=None)
    def test_create_hobby_with_tags(self, _mock_img, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        db.commit()
        hobby = create_hobby(db, p.id, "Title", "desc", "tag1, tag2", None)
        assert len(hobby.tags) == 2

    # TP-HS24
    @patch("services.hobby_service.delete_image")
    @patch("services.hobby_service.save_upload_image", return_value=None)
    def test_delete_hobby_removes_record(self, _mock_img, _mock_del, db):
        u = _make_user(db)
        p = _make_persona(db, u)
        db.commit()
        hobby = create_hobby(db, p.id, "Title", "desc", "", None)
        hobby_id = hobby.id
        delete_hobby(db, hobby)
        assert db.query(Hobby).filter(Hobby.id == hobby_id).first() is None
