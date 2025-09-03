Perfect — two routes, two very different input contracts, two different aggregation targets. Below are tight, end-to-end JSON flows for both, aligned to your PRD and your DB.

1) POST /v1/contentGenerationForAHS (teacher-led, topic+context mandatory)
1.1 Request (AHS)
{
  "teacher_class_id": "TC_10A_PHY_2025",
  "session_id": "Ssn_2025_08_20_1",
  "duration_minutes": 35,
  "grade_level": "10",
  "curriculum_goal": "CBSE_Physics_Grade10",
  "topic": "Reflection and Refraction",
  "context_refs": {
    "lesson_script_id": "LS_abc123",
    "in_class_question_ids": ["Q_101","Q_102","Q_103"]
  },
  "learning_gaps": ["confuse_focus_focal_length"], 
  "modes": [
    "learn_by_reading",
    "learn_by_watching",
    "learn_by_solving",
    "learn_by_writing",
    "learn_by_doing",
    "learn_by_playing",
    "learn_by_questioning_debating",
    "learn_by_listening_speaking",
    "learning_by_assessment"
  ],
  "options": {
    "problems": { "count": 6, "types": ["MCQ","FITB"], "progressive_difficulty": true },
    "videos": { "max": 3, "min_duration": 3, "max_duration": 10 },
    "writing_prompts": { "count": 2, "length": "short" },
    "safety_constraints": { "experiments_home_safe": true }
  }
}

1.2 Immediate 202 (job created)
{
  "job_id": "JOB_AHS_7f2a",
  "status": "pending"
}

1.3 Orchestrator plan (internal)
{
  "job_id": "JOB_AHS_7f2a",
  "status": "in_progress",
  "orchestrator_plan": {
    "features_used": [1,2,3,4,5,6,8,9,10],
    "skipped": [],
    "routing_reason": "AHS requires topic+context; gaps optional; compose multi-format set."
  },
  "tasks": [
    { "task_id":"T1", "type":"learn_by_reading", "status":"queued" },
    { "task_id":"T2", "type":"learn_by_watching", "status":"queued" },
    { "task_id":"T3", "type":"learn_by_solving", "status":"queued" },
    { "task_id":"T4", "type":"learn_by_writing", "status":"queued" },
    { "task_id":"T5", "type":"learn_by_doing", "status":"queued" },
    { "task_id":"T6", "type":"learn_by_playing", "status":"queued" },
    { "task_id":"T7", "type":"learn_by_questioning_debating", "status":"queued" },
    { "task_id":"T8", "type":"learn_by_listening_speaking", "status":"queued" },
    { "task_id":"T9", "type":"learning_by_assessment", "status":"waiting_dependencies", "depends_on":["T1","T3","T4"] }
  ],
  "progress": 0
}

1.4 Representative sub-agent outputs (artifacts)
(each saved to content_store and referenced later; trimmed for clarity)
T1 – Learn by Reading (Feature 1)
{
  "content_id": "C_RD_001",
  "type": "reading_notes",
  "payload": {
    "five_min_summary": "Light reflects with angle i = r; refraction follows Snell's law n1 sin i = n2 sin r...",
    "sections": [
      { "title":"Key Terms", "items":["principal axis","pole","focus","focal length"] },
      { "title":"Concept Map", "svg_diagram_id":"VIZ_reflection_refraction_01" }
    ],
    "glossary":[{"term":"focal length","def":"Distance from pole to focus"}],
    "memory_hacks":["F-Focus is Fixed at F","Index ↑ → speed ↓ → bends toward normal"],
    "gap_explanations":[
      {"gap":"confuse_focus_focal_length","text":"Focus is a point; focal length is the distance P→F..."}
    ],
    "visual_questions":[
      "In the diagram, which ray passes through the focus after reflection?"
    ]
  },
  "meta": { "grade":"10", "topic":"Reflection and Refraction" }
}

T2 – Learn by Watching (Feature 3)
{
  "content_id": "C_VID_001",
  "type": "video_refs",
  "payload": [
    { "title":"Snell's Law in 5 minutes", "youtube_id":"abcX1", "summary":"Derives n1 sin i = n2 sin r with examples", "duration_min":5 },
    { "title":"Concave Mirror Ray Diagrams", "youtube_id":"defY2", "summary":"Step-by-step ray construction; locating focus", "duration_min":7 }
  ]
}

T3 – Learning by Solving (Feature 6)
{
  "content_id": "C_PROB_001",
  "type": "problem_set",
  "payload": {
    "problems": [
      { "id":"P1","type":"MCQ","difficulty":"easy","stem":"For a concave mirror f=20 cm...", "options":["..."],"answer_key":"B","explanation":"..." },
      { "id":"P2","type":"FITB","difficulty":"medium","stem":"n1 sin i = __ sin r", "answer_key":"n2" },
      { "id":"P3","type":"MCQ","difficulty":"hard","stem":"A ray enters glass n=1.5 at 40°...", "options":["..."],"answer_key":"D","explanation":"..." }
    ],
    "scheduling_hints":[{"weak_area":"focal_length_vs_focus","resurface_after_minutes":120}]
  }
}

T4 – Learn by Writing (Feature 2)
{
  "content_id": "C_WRITE_001",
  "type": "writing_prompts",
  "payload": {
    "prompts":[
      "In your own words, differentiate focus vs focal length with a labeled sketch.",
      "Explain why a ray bends toward the normal when entering a denser medium."
    ]
  }
}

T5 – Learn by Doing (Feature 5)
{
  "content_id": "C_DO_001",
  "type": "hands_on_task",
  "payload": {
    "title":"Measure focal length using sunlight and a concave mirror",
    "materials":["Concave mirror","Ruler","Paper"],
    "steps":["Hold mirror...","Adjust until sharp image...","Measure P→F distance"],
    "post_task_questions":["If you double object distance, what changes?"]
  }
}

T6 – Learn by Playing (Feature 4)
{
  "content_id": "C_GAME_001",
  "type": "game_link",
  "payload": { "url":"https://games.pupil/launch?gaps=confuse_focus_focal_length" }
}

T7 – Learn by Questioning & Debating (Feature 8)
{
  "content_id": "C_DEB_001",
  "type": "debate_setup",
  "payload": {
    "topic":"Does refraction conserve image 'truth'?",
    "format":"Socratic",
    "persona":"Ibn al-Haytham",
    "rules":["Ask 'why' thrice","Cite a law each claim"],
    "conversation_prompts":["Why does bending occur at boundaries?","What if n1 < n2 reversed?"]
  }
}

T8 – Learn by Listening & Speaking (Feature 9)
{
  "content_id": "C_AUDIO_001",
  "type": "audio_script",
  "payload": {
    "tone":"informative",
    "script":"Narrator: Imagine sunlight hitting a lake...",
    "check_questions":["State Snell's law.","Define focal length."]
  }
}

T9 – Learning by Assessment (Feature 10)
{
  "content_id": "C_AH_QA_001",
  "type": "mini_assessment",
  "payload": {
    "questions":[
      {"type":"MCQ","stem":"At air-glass boundary...", "options":["..."],"answer_key":"A","why":"angle to normal decreases"},
      {"type":"Short","stem":"Define principal focus of a concave mirror.","answer_key":"Point on principal axis..."}
    ],
    "coverage_summary":["focus vs focal length","Snell's law application"]
  }
}

1.5 Aggregation → DB write (maps to your sessions.afterHourSession)
{
  "_id": "Ssn_2025_08_20_1",
  "afterHourSession": {
    "texts": ["C_RD_001","C_WRITE_001","C_DO_001","C_DEB_001","C_AUDIO_001"],
    "videos": ["C_VID_001"],
    "games": ["C_GAME_001"],
    "practiceQuestions": { "artifact_id":"C_PROB_001" },
    "assessmentQuestions": { "artifact_id":"C_AH_QA_001" },
    "status": "ready"
  }
}

1.6 Final GET (assembled AHS response)
{
  "job_id": "JOB_AHS_7f2a",
  "status": "completed",
  "session_id": "Ssn_2025_08_20_1",
  "artifacts": [
    "C_RD_001","C_VID_001","C_PROB_001","C_WRITE_001",
    "C_DO_001","C_GAME_001","C_DEB_001","C_AUDIO_001","C_AH_QA_001"
  ],
  "links": {
    "session_doc": "sessions/Ssn_2025_08_20_1",
    "preview": "sessions/Ssn_2025_08_20_1/preview"
  }
}


2) POST /v1/contentGenerationForRemedies (personalized, learning_gaps mandatory, spiral 2–3 loops)
2.1 Request (Remedy)
{
  "teacher_class_id": "TC_10A_PHY_2025",
  "student_id": "STU_5942",
  "duration_minutes": 20,
  "learning_gaps": [
    { "code":"confuse_focus_focal_length", "evidence":["inclass:Q_102 wrong","AHS:mini_assessment Q2 wrong"] }
  ],
  "context_refs": {
    "recent_session_ids": ["Ssn_2025_08_20_1"],
    "lesson_script_id": "LS_abc123",
    "recent_performance": { "accuracy_last_24h": 0.58, "avg_time_sec": 48 }
  },
  "modes": [
    "learn_by_reading",
    "learn_by_solving",
    "learn_by_playing",
    "learn_by_listening_speaking",
    "learning_by_assessment"
  ],
  "options": {
    "max_loops": 3,
    "spiral_enable": true,
    "problem_count": 4
  }
}

2.2 Immediate 202
{
  "job_id": "JOB_REM_d91e",
  "status": "pending"
}

2.3 Diagnostics & Spiral plan (internal)
{
  "job_id": "JOB_REM_d91e",
  "status": "in_progress",
  "diagnosis": {
    "gap_classification": "fundamental", 
    "confidence": 0.74,
    "evidence_refs": ["Q_102","C_AH_QA_001#Q2"]
  },
  "spiral_path": [
    { "loop":1, "target_topic":"Ray diagrams for concave mirror", "goal":"differentiate focus vs focal length" },
    { "loop":2, "target_topic":"Basic mirror terms (pole, principal axis)", "goal":"anchor vocabulary" }
  ],
  "selected_features": [1,4,6,9,10]
}

2.4 Loop 1 artifacts (target_topic: Ray diagrams)
Reading (targeted micro-note)
{
  "content_id":"RMD_RD_L1_001",
  "type":"micro_notes",
  "payload":{
    "bullets":[
      "Focus (F): point where parallel rays converge.",
      "Focal length (f): distance PF (in cm)."
    ],
    "1_min_sketch_prompt":"Draw principal axis, P, F; mark f as PF."
  }
}

Playing (gap-focused game)
{
  "content_id":"RMD_GAME_L1_001",
  "type":"game_link",
  "payload":{"url":"https://games.pupil/launch?gaps=confuse_focus_focal_length&level=L1"}
}

Solving (2 items)
{
  "content_id":"RMD_PROB_L1_001",
  "type":"micro_problem_set",
  "payload":{
    "problems":[
      {"id":"L1_P1","type":"MCQ","stem":"f=15 cm. Distance PF equals __","options":["15 cm","F","P"],"answer_key":"15 cm"},
      {"id":"L1_P2","type":"Short","stem":"Define focus in one line.","answer_key":"Point on principal axis where parallel rays meet"}
    ]
  }
}

Listening (30-60s audio script)
{
  "content_id":"RMD_AUD_L1_001",
  "type":"micro_audio_script",
  "payload":{
    "script":"Imagine sun rays are parallel soldiers marching...",
    "check":["State difference focus vs focal length."]
  }
}

Assessment (2 checks)
{
  "content_id":"RMD_QA_L1_001",
  "type":"micro_assessment",
  "payload":{
    "questions":[
      {"type":"FITB","stem":"f is the distance from __ to __","answer_key":"P; F"},
      {"type":"MCQ","stem":"Which is a point?","options":["Focus","Focal length"],"answer_key":"Focus"}
    ],
    "pass_threshold": 0.8
  }
}

Loop 1 result (internal)
{
  "loop": 1,
  "score": 0.5,
  "result": "fail",
  "next_action": "descend_spiral"
}

2.5 Loop 2 artifacts (more foundational)
{
  "content_id":"RMD_RD_L2_001",
  "type":"micro_notes",
  "payload":{
    "bullets":[
      "Pole (P): geometric center of mirror.",
      "Principal axis: straight line through P and center."
    ],
    "analogy":"Think of P as the mirror's 'zero marker'; F is a landmark on that line."
  }
}

{
  "content_id":"RMD_PROB_L2_001",
  "type":"micro_problem_set",
  "payload":{
    "problems":[
      {"id":"L2_P1","type":"Label","stem":"Label P, F on a sketch; mark f=10 cm"},
      {"id":"L2_P2","type":"MCQ","stem":"Which term is a distance?","options":["Focus","Focal length"],"answer_key":"Focal length"}
    ]
  }
}

{
  "content_id":"RMD_QA_L2_001",
  "type":"micro_assessment",
  "payload":{
    "questions":[
      {"type":"Short","stem":"Define principal axis.","answer_key":"Line through the pole and center"},
      {"type":"MCQ","stem":"PF is called?","options":["Focus","Focal length"],"answer_key":"Focal length"}
    ],
    "pass_threshold": 0.8
  }
}

Loop 2 result (internal)
{
  "loop": 2,
  "score": 0.9,
  "result": "pass",
  "next_action": "exit_spiral"
}

2.6 Aggregation → reporting & links (maps to your student_reports.remedy_report)
{
  "_id": "STU_5942",
  "report": {
    "remedy_report": [
      {
        "remedyId": "REM_2025_08_20_STU_5942",
        "date": "2025-08-20",
        "time": "20:05",
        "topic": "Focus vs Focal length (Physics)",
        "actionTaken": "Two-loop spiral; micro-notes, problems, game, audio; re-assessed.",
        "outcome": "Gap resolved",
        "learning_gaps": "confuse_focus_focal_length",
        "remarks": "Passed loop-2 with 90%",
        "report_url": "content_store/REM_2025_08_20_STU_5942"
      }
    ]
  }
}

2.7 Final GET (assembled Remedy response)
{
  "job_id": "JOB_REM_d91e",
  "status": "completed",
  "student_id": "STU_5942",
  "loops_executed": 2,
  "outcome": "resolved",
  "artifacts": [
    "RMD_RD_L1_001","RMD_GAME_L1_001","RMD_PROB_L1_001","RMD_AUD_L1_001","RMD_QA_L1_001",
    "RMD_RD_L2_001","RMD_PROB_L2_001","RMD_QA_L2_001"
  ],
  "next_actions": [
    { "type":"spaced_recall", "after_minutes": 180, "artifact":"RMD_QA_L2_001" }
  ],
  "links": {
    "student_report_entry": "student_reports/STU_5942#REM_2025_08_20_STU_5942"
  }
}

2.8 Status polling (same for both routes)
{
  "job_id":"JOB_AHS_7f2a",
  "status":"partial",
  "progress":60,
  "task_statuses":[
    {"task_id":"T1","type":"learn_by_reading","status":"completed"},
    {"task_id":"T2","type":"learn_by_watching","status":"completed"},
    {"task_id":"T3","type":"learn_by_solving","status":"in_progress"},
    {"task_id":"T9","type":"learning_by_assessment","status":"waiting_dependencies"}
  ],
  "error": null
}


Contract summary (so you can wire clients fast)
AHS endpoint (topic+context required; gaps optional):


Input keys that matter: teacher_class_id, session_id, duration_minutes, grade_level, curriculum_goal, topic, context_refs, learning_gaps?, modes.


Output aggregates into sessions.afterHourSession.* and returns artifact ids.


Remedy endpoint (gaps required; student-specific; spiral):


Input keys that matter: teacher_class_id, student_id, duration_minutes, learning_gaps[], context_refs, modes, options.spiral/max_loops.


Output logs to student_reports.remedy_report[*].report_url and returns artifacts + loop outcomes.


If you want, I’ll now drop the exact Pydantic schemas for these two payloads and the FastAPI route stubs you can paste into your project.

