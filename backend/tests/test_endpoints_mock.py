"""Endpoint tests with the LLM call mocked out."""
import pytest


@pytest.fixture
def mock_llm(monkeypatch):
    """Patch llm.chat_json to return canned JSON per interaction type."""
    canned = {
        "explain_error": {
            "explanation": "You are calling .length on a None value.",
            "root_cause": "Variable was never assigned.",
            "suggested_fix": "Initialize the variable before use.",
            "corrected_code": "x = []\nprint(len(x))",
            "language": "python",
        },
        "generate_code": {
            "code": "def add(a, b):\n    return a + b\n",
            "language": "python",
            "explanation": "Simple addition.",
            "assumptions": ["a and b are numeric"],
        },
        "review_code": {
            "summary": "Code is short; minor style issue.",
            "issues": [
                {"type": "style", "severity": "info", "description": "Use snake_case.", "line": 1}
            ],
            "improved_code": "def my_func():\n    pass\n",
            "language": "python",
        },
    }

    # Per-call routing based on what's in the user prompt
    def fake_chat_json(system, user, *, model=None, temperature=0.2):
        if "Review the following code" in user:
            return canned["review_code"]
        if "Task:" in user:
            return canned["generate_code"]
        return canned["explain_error"]

    import app.llm as llm_module
    monkeypatch.setattr(llm_module, "chat_json", fake_chat_json)
    # The agent module imported llm before patching; patch its reference too
    import app.services.agent as agent_module
    monkeypatch.setattr(agent_module.llm, "chat_json", fake_chat_json)


def test_explain_error(client, mock_llm):
    r = client.post(
        "/api/explain-error",
        json={"error_message": "NoneType has no len()", "code": "print(len(x))", "language": "python"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["root_cause"]
    assert body["suggested_fix"]


def test_generate_code(client, mock_llm):
    r = client.post(
        "/api/generate-code",
        json={"prompt": "Write a function that adds two numbers", "language": "python"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "def add" in body["code"]
    assert body["language"] == "python"
    assert isinstance(body["assumptions"], list)


def test_review_code(client, mock_llm):
    r = client.post(
        "/api/review-code",
        json={"code": "def MyFunc():\n    pass\n", "language": "python"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]
    assert isinstance(body["issues"], list)
    assert body["issues"][0]["type"] == "style"


def test_history_records_interactions(client, mock_llm):
    # Drive one of each
    client.post("/api/explain-error", json={"error_message": "x"})
    client.post("/api/generate-code", json={"prompt": "hello world"})
    client.post("/api/review-code", json={"code": "x=1"})

    r = client.get("/api/history")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 3
    types = {i["type"] for i in items}
    assert types == {"explain_error", "generate_code", "review_code"}

    # Detail
    item_id = items[0]["id"]
    r2 = client.get(f"/api/history/{item_id}")
    assert r2.status_code == 200
    detail = r2.json()
    assert detail["request_json"]
    assert detail["response_json"]


def test_history_filter(client, mock_llm):
    client.post("/api/explain-error", json={"error_message": "x"})
    client.post("/api/generate-code", json={"prompt": "p"})
    r = client.get("/api/history", params={"type": "generate_code"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["type"] == "generate_code"


def test_validation_error(client, mock_llm):
    r = client.post("/api/explain-error", json={"error_message": ""})
    assert r.status_code == 422
