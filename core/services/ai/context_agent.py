from datetime import datetime, timedelta
from services.db_operations.assessment_db import (
    get_pyq_examples,
    get_topics_by_date_range,
    get_random_past_topics,
    download_and_parse_file,
    get_learning_outcomes_by_topics
)

class ContextAgent:
    @staticmethod
    async def gather_context(
        exam_type: str,
        previous_topics: list = None,
        learning_gaps: list = None,
        file_url: str = None,
        self_assessment_mode: str = None,
        subject: str = None,
        grade: int = None
    ):
        context = {}

        # 1️⃣ Determine topic selection based on exam_type
        today = datetime.utcnow()
        topics = []

        if exam_type == "weekly":
            # 100% from last 7 days
            #flag-1 the get_topics_by_date_range is not working as expected because the date range is not correct 
            topics = await get_topics_by_date_range(
                today - timedelta(days=7), 
                today, 
                subject=subject, 
                grade=grade
            )

        elif exam_type == "monthly":
            # 70% from last 30 days, 30% from previous topics or random past
            recent_topics = await get_topics_by_date_range(
                today - timedelta(days=30), 
                today, 
                subject=subject, 
                grade=grade
            )
            
            if previous_topics:
                past_topics = previous_topics
            else:
                past_topics = await get_random_past_topics(
                    limit=max(1, len(recent_topics) // 3),
                    subject=subject,
                    grade=grade
                )
            
            # 70/30 split
            recent_count = int(len(recent_topics) * 0.7)
            topics = recent_topics[:recent_count] + past_topics

        elif exam_type == "quarterly":
            # 70% from last 90 days, 30% from previous topics or random past
            recent_topics = await get_topics_by_date_range(
                today - timedelta(days=90), 
                today, 
                subject=subject, 
                grade=grade
            )
            
            if previous_topics:
                past_topics = previous_topics
            else:
                past_topics = await get_random_past_topics(
                    limit=max(1, len(recent_topics) // 3),
                    subject=subject,
                    grade=grade
                )
            
            # 70/30 split
            recent_count = int(len(recent_topics) * 0.7)
            topics = recent_topics[:recent_count] + past_topics

        elif exam_type == "self_assessment":
            # PRD: 65/35 split (learning_gaps vs learning_outcomes). We don't have learning_gaps in DB, so emulate:
            # Use recent/past topics as proxies, but we will annotate the split in context for the prompt.
            if self_assessment_mode == "random":
                topics = await get_random_past_topics(
                    limit=10,
                    subject=subject,
                    grade=grade
                )
            elif self_assessment_mode == "weekly":
                topics = await get_topics_by_date_range(
                    today - timedelta(days=7), 
                    today, 
                    subject=subject, 
                    grade=grade
                )
            elif self_assessment_mode == "monthly":
                recent_topics = await get_topics_by_date_range(
                    today - timedelta(days=30), 
                    today, 
                    subject=subject, 
                    grade=grade
                )
                past_topics = await get_random_past_topics(
                    limit=max(1, len(recent_topics) // 2),
                    subject=subject,
                    grade=grade
                )
                # Emulate 65/35 split by proportionally selecting from recent (as proxy for gaps) and outcomes
                recent_count = int(len(recent_topics) * 0.65)
                topics = recent_topics[:recent_count] + past_topics[: max(0, len(past_topics) - recent_count)]
            else:
                raise ValueError(f"Invalid self_assessment_mode: {self_assessment_mode}")
        else:
            raise ValueError(f"Unknown exam_type: {exam_type}")

        context["selected_topics"] = topics

        # 2️⃣ Get learning outcomes for selected topics
        if topics:
            context["learning_outcomes"] = await get_learning_outcomes_by_topics(topics)
        else:
            context["learning_outcomes"] = []

        # 3️⃣ Process learning gaps (if provided) or derive from context
        if learning_gaps:
            context["learning_gaps"] = learning_gaps
        else:
            # For self_assessment, derive gaps from recent topics as proxy
            if exam_type == "self_assessment":
                context["learning_gaps"] = topics[:int(len(topics) * 0.65)]  # 65% as gaps
            else:
                context["learning_gaps"] = []

        # 4️⃣ Add grade to context for question generation
        context["grade"] = grade

        # Annotate intended split so the LLM follows PRD semantics
        if exam_type == "self_assessment":
            context["intended_split"] = {"learning_gaps": 65, "learning_outcomes": 35}
        elif exam_type in ("monthly", "quarterly"):
            context["intended_split"] = {"recent": 70, "past": 30}
        elif exam_type == "weekly":
            context["intended_split"] = {"recent": 100}

        # 3️⃣ Use PYQ Tool (Few-shot examples) - enhanced with template requirements
        # Extract question types and difficulty from schema if available
        question_types = None
        difficulty = None
        
        # Get examples that match the assessment requirements
        context["examples"] = await get_pyq_examples(
            topics=topics, 
            limit=5, 
            difficulty=difficulty,
            question_types=question_types
        )

        # 4️⃣ Process file if provided
        if file_url:
            try:
                context["file_content"] = download_and_parse_file(file_url)
            except Exception as e:
                context["file_content"] = f"Error processing file: {str(e)}"

        return context
