import pytest


@pytest.mark.asyncio
async def test_assessment_agent_minimal(monkeypatch):
    from core.agents.assessment_agent import AssessmentAgent

    agent = AssessmentAgent()

    class FakeGraph:
        async def ainvoke(self, params):
            return {"questions": [{"stem": "s"}]}

    # replace compiled graph object with fake
    monkeypatch.setattr(agent, "graph", FakeGraph())
    res = await agent.execute({"target_exam": "X", "exam_type": "Y", "subject": "Physics"})
    assert res["status"] == "completed"
    assert res["result"]["questions"][0]["stem"] == "s"


@pytest.mark.asyncio
async def test_content_agent_modes(monkeypatch):
    from core.agents.content_agent import ContentAgent

    agent = ContentAgent()

    class FakeCompiled:
        async def ainvoke(self, params):
            return {"db_handles": {"AHS": "sessions/1"}}

    class FakeGraph:
        def __call__(self, active_modes):
            return self

        def compile(self):
            return FakeCompiled()

    monkeypatch.setattr(agent, "graph", FakeGraph)
    res = await agent.execute({"route": "AHS", "modes": ["learn_by_reading"], "req": {"topic": "T"}})
    assert res["db_handles"]["AHS"] == "sessions/1"


@pytest.mark.asyncio
async def test_remedy_agent_minimal(monkeypatch):
    from core.agents.remedy_agent import RemedyAgent

    agent = RemedyAgent()

    class FakeCompiled:
        async def ainvoke(self, params):
            return {"final_plans": [{"gap_type": "conceptual"}]}

    class FakeGraph:
        def __call__(self):
            return self

        def compile(self):
            return FakeCompiled()

    monkeypatch.setattr(agent, "graph", FakeGraph)
    res = await agent.execute({"classified_gaps": [], "student_id": "S1", "teacher_class_id": "TC1"})
    assert res["final_plans"][0]["gap_type"] == "conceptual"


