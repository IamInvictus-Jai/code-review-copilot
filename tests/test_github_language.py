import sys
import types
import unittest

# ── Stub heavy deps so the module-level `gh = Github(...)` call doesn't fail ──
_fake_github_mod = types.ModuleType("github")
_fake_github_mod.Github = lambda *a, **kw: None
_fake_github_mod.GithubException = Exception
sys.modules.setdefault("github", _fake_github_mod)

_fake_requests = types.ModuleType("requests")
sys.modules.setdefault("requests", _fake_requests)

_fake_models = types.ModuleType("app.models")
_fake_models.PRReviewResult = object
sys.modules.setdefault("app.models", _fake_models)

_fake_diff_parser = types.ModuleType("app.utils.diff_parser")
_fake_diff_parser.annotate_diff = lambda x: x
sys.modules.setdefault("app.utils", types.ModuleType("app.utils"))
sys.modules.setdefault("app.utils.diff_parser", _fake_diff_parser)

from app.services.github import get_language_from_filename  # noqa: E402


class GetLanguageFromFilenameTests(unittest.TestCase):

    # ── Well-known extensions ──────────────────────────────────────────────
    def test_python_file(self):
        self.assertEqual(get_language_from_filename("src/utils.py"), "python")

    def test_javascript_file(self):
        self.assertEqual(get_language_from_filename("src/index.js"), "javascript")

    def test_typescript_file(self):
        self.assertEqual(get_language_from_filename("src/app.ts"), "typescript")

    def test_tsx_file(self):
        self.assertEqual(get_language_from_filename("components/Button.tsx"), "tsx")

    def test_java_file(self):
        self.assertEqual(get_language_from_filename("Main.java"), "java")

    def test_go_file(self):
        self.assertEqual(get_language_from_filename("main.go"), "go")

    def test_rust_file(self):
        self.assertEqual(get_language_from_filename("lib.rs"), "rust")

    def test_html_file(self):
        self.assertEqual(get_language_from_filename("index.html"), "html")

    def test_css_file(self):
        self.assertEqual(get_language_from_filename("styles.css"), "css")

    def test_yaml_file(self):
        self.assertEqual(get_language_from_filename("config.yaml"), "yaml")

    def test_yml_alias(self):
        self.assertEqual(get_language_from_filename(".github/workflows/ci.yml"), "yaml")

    def test_json_file(self):
        self.assertEqual(get_language_from_filename("package.json"), "json")

    def test_shell_script(self):
        self.assertEqual(get_language_from_filename("deploy.sh"), "bash")

    def test_sql_file(self):
        self.assertEqual(get_language_from_filename("schema.sql"), "sql")

    # ── Special filenames ──────────────────────────────────────────────────
    def test_dockerfile_exact_name(self):
        self.assertEqual(get_language_from_filename("Dockerfile"), "dockerfile")

    def test_dockerfile_in_subdir(self):
        self.assertEqual(get_language_from_filename("docker/Dockerfile"), "dockerfile")

    def test_makefile(self):
        self.assertEqual(get_language_from_filename("Makefile"), "makefile")

    def test_docker_compose_yml(self):
        self.assertEqual(get_language_from_filename("docker-compose.yml"), "yaml")

    # ── Fallback behaviour ─────────────────────────────────────────────────
    def test_unknown_extension_returns_bare_extension(self):
        # e.g. ".xyz" → "xyz" so the fence is at least annotated
        self.assertEqual(get_language_from_filename("foo.xyz"), "xyz")

    def test_extensionless_file_returns_empty_string(self):
        self.assertEqual(get_language_from_filename("LICENCE"), "")

    def test_case_insensitive_extension(self):
        # .PY should resolve the same as .py
        self.assertEqual(get_language_from_filename("Script.PY"), "python")


if __name__ == "__main__":
    unittest.main()
