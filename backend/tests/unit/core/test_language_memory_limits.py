"""Test cấu hình giới hạn bộ nhớ của từng ngôn ngữ khi gửi lên Judge0.

Bối cảnh: JVM cần reserve code cache + metaspace (~245 MB) trước khi chạy.
Nếu để mặc định của Judge0 (128 MB) thì Java luôn NZEC với thông điệp
"Could not reserve enough space for code cache" — tức là ngôn ngữ Java được
hiện trong danh sách lựa chọn nhưng thực tế KHÔNG chấm được.
"""

from app.core import config


def test_java_has_enough_memory_limit_for_jvm():
    """Java cần memory_limit đủ lớn, không dùng mặc định 128 MB của Judge0."""
    java = config.LANGUAGES["java"]

    assert java.memory_limit_kb is not None
    assert java.memory_limit_kb >= 6_144_000


def test_java_memory_limit_matches_judge0_conf_max():
    """Trần của judge0.conf (MAX_MEMORY_LIMIT) phải >= giới hạn của Java."""
    java = config.LANGUAGES["java"]

    assert java.memory_limit_kb is not None
    assert java.memory_limit_kb <= 6_144_000


def test_python_and_c_do_not_need_extra_memory():
    """Python/C chạy với ~4-7 MB nên để Judge0 tự giới hạn."""
    assert config.LANGUAGES["python"].memory_limit_kb is None
    assert config.LANGUAGES["c"].memory_limit_kb is None


def test_javascript_keeps_its_memory_limit():
    """Node.js cũng cần RAM riêng (đã cấu hình từ trước)."""
    assert config.LANGUAGES["javascript"].memory_limit_kb == 2_048_000


def test_all_five_languages_are_configured():
    """Dự án chốt hỗ trợ đủ 5 ngôn ngữ (docs/api-design-problem.md)."""
    assert set(config.LANGUAGES) >= {"python", "javascript", "c", "cpp", "java"}


def test_every_language_maps_to_a_judge0_id():
    for name, language in config.LANGUAGES.items():
        assert language.judge0_id > 0, name
