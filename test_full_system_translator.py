import json
import re
import unittest
import urllib.error
from unittest.mock import patch

import full_system_translator as translator


class TranslationContextTests(unittest.TestCase):
    def test_quoted_product_name_does_not_count_as_mixed_language_residue(self):
        source = (
            '"ROBOMAKER Artificial Intelligence Robot Education System" '
            "strives to reduce the difficulty of entry and use of the products."
        )
        translation = (
            '"ROBOMAKER Artificial Intelligence Robot Education System" '
            "nhằm giảm rào cản tiếp cận và sử dụng sản phẩm."
        )

        self.assertFalse(translator.has_english_residue(source, translation))

    def test_detects_english_phrase_left_in_vietnamese_translation(self):
        self.assertTrue(
            translator.has_english_residue(
                "The robot has high torque and speed",
                "Robot có high torque và tốc độ",
            )
        )

    def test_batch_retranslates_mixed_language_output_before_returning(self):
        responses = [
            "ZMBATCH0000X Robot có high torque và tốc độ",
            "Robot có mô-men xoắn cao và tốc độ",
        ]

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps([[ [self.value, None, None, None] ], None, "en"]).encode("utf-8")

        with patch.object(
            translator.urllib.request,
            "urlopen",
            side_effect=[FakeResponse(value) for value in responses],
        ) as urlopen:
            result = translator.translate_batch_google(
                ["The robot has high torque and speed"]
            )

        self.assertEqual(result, ["Robot có mô-men xoắn cao và tốc độ"])
        self.assertEqual(urlopen.call_count, 2)

    def test_allows_preserved_technical_terms_in_vietnamese_translation(self):
        self.assertFalse(
            translator.has_english_residue(
                "AI Vision Module with USB camera",
                "Mô-đun thị giác AI với camera USB",
            )
        )

    def test_batch_is_split_after_retries_for_server_error(self):
        requests = []

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps([[ [self.value, None, None, None] ], None, "en"]).encode("utf-8")

        def fake_urlopen(request, **_kwargs):
            query = translator.urllib.parse.parse_qs(
                translator.urllib.parse.urlparse(request.full_url).query
            )["q"][0]
            requests.append(query)
            markers = re.findall(r"ZMBATCH\d{4}X", query)
            if len(markers) > 1:
                raise urllib.error.HTTPError(
                    request.full_url, 500, "Internal Server Error", {}, None
                )
            return FakeResponse(markers[0] + " Xin chào")

        with (
            patch.object(translator, "GOOGLE_TRANSLATE_MAX_RETRIES", 0),
            patch.object(
                translator.urllib.request, "urlopen", side_effect=fake_urlopen
            ),
        ):
            result = translator.translate_batch_google(["Hello", "Goodbye"])

        self.assertEqual(result, ["Xin chào", "Xin chào"])
        self.assertEqual(len(requests), 3)

    def test_google_request_retries_temporary_server_error(self):
        response_data = [[["Xin chào", None, None, None]], None, "en"]
        response = type(
            "FakeResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *_args: False,
                "read": lambda self: json.dumps(response_data).encode("utf-8"),
            },
        )()
        http_error = urllib.error.HTTPError(
            "https://translate.googleapis.com/",
            500,
            "Internal Server Error",
            {},
            None,
        )

        with (
            patch.object(
                translator.urllib.request,
                "urlopen",
                side_effect=[http_error, response],
            ) as urlopen,
            patch.object(translator.time, "sleep") as sleep,
        ):
            self.assertEqual(
                translator.request_google_translation("Hello"),
                "Xin chào",
            )

        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_google_request_reports_server_error_after_retry_limit(self):
        error = urllib.error.HTTPError(
            "https://translate.googleapis.com/",
            500,
            "Internal Server Error",
            {},
            None,
        )

        with (
            patch.object(translator, "GOOGLE_TRANSLATE_MAX_RETRIES", 2),
            patch.object(
                translator.urllib.request,
                "urlopen",
                side_effect=error,
            ) as urlopen,
            patch.object(translator.time, "sleep"),
        ):
            with self.assertRaises(translator.GoogleTranslateHTTPError) as raised:
                translator.request_google_translation("Hello")

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(urlopen.call_count, 3)

    def test_html_units_keep_sentence_and_leaf_container_context(self):
        html = (
            "<div><p><span>Electronic</span><span> Accessories</span></p>"
            "<div>Operating voltage: <span>5V</span></div></div>"
        )

        self.assertEqual(
            translator.collect_html_translation_units(html),
            {
                "<p><span>Electronic</span><span> Accessories</span></p>",
                "<div>Operating voltage: <span>5V</span></div>",
            },
        )

    def test_html_translation_preserves_markup_and_contextual_spacing(self):
        html = (
            "<div><p><span>Electronic</span><span> Accessories</span></p>"
            "<div>Operating voltage: <span>5V</span></div></div>"
        )
        translations = {
            translator.normalize_html_unit(
                "<p><span>Electronic</span><span> Accessories</span></p>"
            ): "<p><span>Phụ kiện</span><span> điện tử</span></p>",
            translator.normalize_html_unit(
                "<div>Operating voltage: <span>5V</span></div>"
            ): "<div>Điện áp hoạt động: <span>5V</span></div>",
        }

        self.assertEqual(
            translator.translate_html_content(html, translations),
            "<div><p><span>Phụ kiện</span><span> điện tử</span></p>"
            "<div>Điện áp hoạt động: <span>5V</span></div></div>",
        )

    def test_batch_translation_restores_html_tags(self):
        response_data = [
            [
                ["ZMBATCH0000X ZMTAG0000X Xin chào ZMTAG0001X", None, None, None]
            ],
            None,
            "en",
        ]

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(response_data).encode("utf-8")

        with patch.object(translator.urllib.request, "urlopen", return_value=FakeResponse()):
            self.assertEqual(
                translator.translate_batch_google(["<p>Hello</p>"]),
                ["<p> Xin chào </p>"],
            )

    def test_batch_translation_splits_when_a_tag_marker_is_lost(self):
        requests = []

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps([[ [self.value, None, None, None] ], None, "en"]).encode("utf-8")

        def fake_urlopen(request, **_kwargs):
            query = translator.urllib.parse.parse_qs(
                translator.urllib.parse.urlparse(request.full_url).query
            )["q"][0]
            requests.append(query)
            markers = list(re.finditer(r"ZMBATCH\d{4}X", query))
            translated_items = []
            for index, marker in enumerate(markers):
                end = markers[index + 1].start() if index + 1 < len(markers) else len(query)
                item = query[marker.end():end]
                tags = re.findall(r"ZMTAG\d{4}X", item)
                if len(markers) > 1 and index == 0:
                    tags = tags[:1]
                if tags:
                    translated_items.append(
                        marker.group(0)
                        + " "
                        + (
                            tags[0] + " Xin chào " + tags[1]
                            if len(tags) > 1
                            else tags[0]
                        )
                    )
                else:
                    translated_items.append(marker.group(0) + " Xin chào")
            return FakeResponse(" ".join(translated_items))

        with patch.object(translator.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = translator.translate_batch_google(
                ["<p>Hello</p>", "<p>Goodbye</p>"]
            )

        self.assertEqual(result, ["<p> Xin chào </p>", "<p> Xin chào </p>"])
        self.assertEqual(len(requests), 3)

    def test_html_tag_restore_accepts_spacing_inserted_into_marker(self):
        restored, invalid = translator.restore_html_tags(
            "ZM TAG 0003 X xin chào",
            {"ZMTAG0003X": "<p>"},
        )

        self.assertIsNone(invalid)
        self.assertEqual(restored, "<p> xin chào")

    def test_batch_translation_falls_back_to_plain_text_when_marker_is_dropped(self):
        requests = []

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps([[ [self.value, None, None, None] ], None, "en"]).encode("utf-8")

        def fake_urlopen(request, **_kwargs):
            query = translator.urllib.parse.parse_qs(
                translator.urllib.parse.urlparse(request.full_url).query
            )["q"][0]
            requests.append(query)
            batch_marker = re.search(r"ZMBATCH\d{4}X", query).group(0)
            if "ZMTAG" in query:
                return FakeResponse(batch_marker + " Chào mừng")
            return FakeResponse(batch_marker + " Xin chào")

        with patch.object(translator.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = translator.translate_batch_google(
                ["<p><span>Hello</span> there</p>"]
            )

        self.assertEqual(result, ["<p><span>Xin chào</span></p>"])
        self.assertEqual(len(requests), 2)
        self.assertNotIn("<", requests[1])
        self.assertIn("Hello there", requests[1])

    def test_batch_translation_splits_and_retries_empty_results_directly(self):
        requests = []

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps([[ [self.value, None, None, None] ], None, "en"]).encode("utf-8")

        def fake_urlopen(request, **_kwargs):
            query = translator.urllib.parse.parse_qs(
                translator.urllib.parse.urlparse(request.full_url).query
            )["q"][0]
            requests.append(query)
            batch_marker = re.search(r"ZMBATCH\d{4}X", query)
            if batch_marker:
                return FakeResponse(batch_marker.group(0))
            return FakeResponse("Xin chào")

        with patch.object(translator.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = translator.translate_batch_google(["Hello", "Goodbye"])

        self.assertEqual(result, ["Xin chào", "Xin chào"])
        self.assertEqual(len(requests), 5)
        self.assertTrue(all("ZMBATCH" not in request for request in requests[1:]))


if __name__ == "__main__":
    unittest.main()
