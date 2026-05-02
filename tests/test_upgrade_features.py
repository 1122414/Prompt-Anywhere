import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.services.pinyin_service import PinyinService
from app.services.search_matcher import SearchMatcher
from app.services.search_ranker import SearchRanker
from app.services.knowledge_base_service import KnowledgeBaseService, PromptMetadata
from app.services.tag_service import TagService
from app.services.usage_service import UsageService
from app.services.vector_store import VectorStore
from app.services.ai_template_service import AITemplateService


class TestPinyinService(unittest.TestCase):
    def setUp(self):
        PinyinService._instance = None
        self.service = PinyinService()

    def tearDown(self):
        PinyinService._instance = None

    def test_full_pinyin(self):
        result = self.service.get_full_pinyin("代码审查")
        self.assertEqual(result, "daimashencha")

    def test_initials(self):
        result = self.service.get_initials("代码审查")
        self.assertEqual(result, "dmsc")

    def test_build_fields(self):
        result = self.service.build_pinyin_fields("简历优化")
        self.assertEqual(result["full"], "jianliyouhua")
        self.assertEqual(result["initials"], "jlyh")
        self.assertIn("jian", result["tokens"])
        self.assertIn("li", result["tokens"])

    def test_empty_text(self):
        self.assertEqual(self.service.get_full_pinyin(""), "")
        self.assertEqual(self.service.get_initials(""), "")


class TestSearchMatcher(unittest.TestCase):
    def setUp(self):
        SearchMatcher._instance = None
        self.matcher = SearchMatcher()

    def tearDown(self):
        SearchMatcher._instance = None

    def test_fuzzy_match_exact(self):
        result = self.matcher.fuzzy_match("代码", "代码审查")
        self.assertTrue(result.matched)
        self.assertGreater(result.score, 80)

    def test_fuzzy_match_typo(self):
        result = self.matcher.fuzzy_match("代码审", "代码审查")
        self.assertTrue(result.matched)
        self.assertGreater(result.score, 60)

    def test_match_pinyin_initials(self):
        result = self.matcher.match_pinyin("dmsc", "daimashencha", "dmsc")
        self.assertTrue(result.matched)

    def test_match_pinyin_full(self):
        result = self.matcher.match_pinyin("daima", "daimashencha", "dmsc")
        self.assertTrue(result.matched)


class TestSearchRanker(unittest.TestCase):
    def setUp(self):
        SearchRanker._instance = None
        self.ranker = SearchRanker()

    def tearDown(self):
        SearchRanker._instance = None

    def test_exact_filename_match(self):
        score = self.ranker.calculate_score(
            keyword="代码审查",
            filename="代码审查",
            category="代码",
            content="审查代码质量",
            path="代码/代码审查.md",
        )
        self.assertGreater(score, 100)

    def test_pinyin_match(self):
        score = self.ranker.calculate_score(
            keyword="daima",
            filename="代码审查",
            category="代码",
            content="审查代码质量",
            path="代码/代码审查.md",
            filename_pinyin="daimashencha",
            filename_initials="dmsc",
        )
        self.assertGreater(score, 50)


class TestKnowledgeBaseService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()
        self.kb_dir = self.data_dir / ".prompt_anywhere"

        os.environ["DATA_DIR"] = str(self.data_dir)
        os.environ["KNOWLEDGE_BASE_DIR"] = "./.prompt_anywhere"
        Config._instance = None
        KnowledgeBaseService._instance = None
        self.config = Config()
        self.kb = KnowledgeBaseService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        if "KNOWLEDGE_BASE_DIR" in os.environ:
            del os.environ["KNOWLEDGE_BASE_DIR"]
        Config._instance = None
        KnowledgeBaseService._instance = None

    def test_sync_file(self):
        self.kb.sync_file("测试/示例.md", "这是示例内容")
        meta = self.kb.get_metadata("测试/示例.md")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.title, "示例")
        self.assertNotEqual(meta.content_hash, "")

    def test_content_hash_change(self):
        self.kb.sync_file("测试/示例.md", "内容A")
        meta1_hash = self.kb.get_metadata("测试/示例.md").content_hash
        self.kb.sync_file("测试/示例.md", "内容B")
        meta2_hash = self.kb.get_metadata("测试/示例.md").content_hash
        self.assertNotEqual(meta1_hash, meta2_hash)

    def test_remove_file(self):
        self.kb.sync_file("测试/示例.md", "内容")
        self.assertIsNotNone(self.kb.get_metadata("测试/示例.md"))
        self.kb.remove_file("测试/示例.md")
        self.assertIsNone(self.kb.get_metadata("测试/示例.md"))

    def test_full_sync(self):
        (self.data_dir / "测试").mkdir()
        (self.data_dir / "测试" / "示例.md").write_text("示例内容", encoding="utf-8")
        self.kb.full_sync()
        items = self.kb.list_all()
        self.assertEqual(len(items), 1)


class TestTagService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        TagService._instance = None
        self.config = Config()
        self.tags = TagService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        TagService._instance = None

    def test_add_and_get_tags(self):
        self.tags.add_tag("代码/审查.md", "代码")
        self.tags.add_tag("代码/审查.md", "质量")
        result = self.tags.get_tags_for_file("代码/审查.md")
        self.assertEqual(sorted(result), ["代码", "质量"])

    def test_get_files_by_tag(self):
        self.tags.add_tag("a.md", "代码")
        self.tags.add_tag("b.md", "代码")
        result = self.tags.get_files_for_tag("代码")
        self.assertEqual(sorted(result), ["a.md", "b.md"])

    def test_remove_tag(self):
        self.tags.add_tag("a.md", "代码")
        self.tags.remove_tag("a.md", "代码")
        self.assertEqual(self.tags.get_tags_for_file("a.md"), [])

    def test_delete_tag(self):
        self.tags.add_tag("a.md", "代码")
        self.tags.delete_tag("代码")
        self.assertEqual(self.tags.list_all_tags(), [])


class TestUsageService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        UsageService._instance = None
        self.config = Config()
        self.usage = UsageService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        UsageService._instance = None

    def test_record_copy(self):
        self.usage.record_copy("a.md")
        self.usage.record_copy("a.md")
        stats = self.usage.get_stats("a.md")
        self.assertEqual(stats["copy_count"], 2)
        self.assertIsNotNone(stats["last_used_at"])

    def test_set_rating(self):
        self.usage.set_rating("a.md", 5)
        stats = self.usage.get_stats("a.md")
        self.assertEqual(stats["rating"], 5)

    def test_rating_clamp(self):
        self.usage.set_rating("a.md", 10)
        stats = self.usage.get_stats("a.md")
        self.assertEqual(stats["rating"], 5)

        self.usage.set_rating("a.md", -1)
        stats = self.usage.get_stats("a.md")
        self.assertEqual(stats["rating"], 0)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        VectorStore._instance = None
        self.config = Config()
        self.store = VectorStore()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        VectorStore._instance = None

    def test_build_and_search(self):
        import numpy as np
        items = ["a.md", "b.md", "c.md"]
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)
        self.store.build_index(items, embeddings)

        query = np.array([0.9, 0.1, 0.0], dtype=np.float32)
        results = self.store.search(query, top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][0], "a.md")


class TestAITemplateService(unittest.TestCase):
    def setUp(self):
        AITemplateService._instance = None
        self.service = AITemplateService()

    def tearDown(self):
        AITemplateService._instance = None

    def test_detect_url(self):
        content = "分析这个页面：https://example.com"
        vars = self.service.detect_variables_rule(content)
        urls = [v for v in vars if v.var_type == "url"]
        self.assertGreater(len(urls), 0)

    def test_detect_platform(self):
        content = "帮我写一个小红书文案"
        vars = self.service.detect_variables_rule(content)
        platforms = [v for v in vars if "平台" in v.name]
        self.assertGreater(len(platforms), 0)

    def test_apply_variables(self):
        content = "分析这个页面：https://example.com"
        vars = self.service.detect_variables_rule(content)
        result = self.service.apply_variables(content, vars)
        self.assertIn("{{", result)
        self.assertIn("}}", result)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPinyinService))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchMatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchRanker))
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeBaseService))
    suite.addTests(loader.loadTestsFromTestCase(TestTagService))
    suite.addTests(loader.loadTestsFromTestCase(TestUsageService))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStore))
    suite.addTests(loader.loadTestsFromTestCase(TestAITemplateService))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
