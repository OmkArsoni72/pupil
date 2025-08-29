Product Requirements Document: Multi-Modal Content Agent
1. Introduction
This document outlines the requirements for a Multi-Modal Content Agent, a system designed to generate diverse and engaging educational content based on user inputs. The agent will leverage advanced generative AI to transform a single topic or prompt into various formats, mirroring the "PupilTutor" learning modes provided as a reference. The agent operates in two primary modes: an After-hour Session mode for teacher-led content, and a Remediation mode for generating content specifically designed to address detected learning gaps.
The primary goal is to empower educators and content creators to quickly produce high-quality, personalized learning materials for different learning styles.
1.1 School-Led Events
The multi-modal content agent is designed to support a structured school-led learning model consisting of three distinct event types:
Class Events: In this model, teachers and students engage with in-class questions, quizzes, or activities. The data and performance from these events are used to identify learning gaps for the entire class as well as for individual students.
After-hour Session: This event focuses on generating class-specific content, often in the form of homework or revision materials. The purpose is to address the collective learning gaps of the class and reinforce the concepts taught during the day.
Remedy Session: This is a highly personalized session designed to solve individual student doubts and address foundational gaps. It utilizes content and a "foundational spiral" approach, drawing on a student's performance and identified gaps from both the Class Events and After-hour Sessions. The remediation process is designed to be iterative, typically in 2-3 loops, to ensure mastery of the concept.
2. Goals & Objectives
To create a versatile content generation tool that supports a wide range of learning formats.
To improve the efficiency of content creation for educational purposes.
To ensure content is contextually relevant, factually accurate, and aligned with specified curriculum goals.
To enable content creators to generate materials for both initial learning and targeted remediation.
To provide a user-friendly interface for generating and customizing content.
3. Target Persona
The primary users of this agent are educators, subject matter experts, and content developers who need to generate educational materials across multiple formats without requiring deep technical knowledge of AI prompts or tools.
4. Content Generation Modes
The agent's functionality is structured around two distinct modes that determine the type of content generated. In both modes, the input will include a composition of learning modes, allowing users to select multiple content types for a single request.
Mode 1: After-hour Session (Teacher-led)
This mode is for generating content to introduce a new topic or for a general learning session led by a teacher. It is primarily driven by the Topic/Concept and Context inputs, which are mandatory. The Learning Gaps input is optional.
Mode 2: Remediation (Personalized for Student)
This mode is for generating content to address a specific learning gap for an individual student. It is primarily driven by the Learning Gaps input, which is mandatory. It uses context from the database to inform its output, but its focus remains on the personalized gap remediation and does not require generating a general topic or period content text.
5. Key Features & Functionality
The agent's functionality is broken down into specific features, each corresponding to one of the identified learning modes. All features will be generated based on the following standard inputs: Teacher Class ID, Duration, Learning Gaps (optional), and Learning Mode Specific Inputs.
Feature 1: Learn by Reading(imp)
Description: Generate comprehensive, bite-sized, and highly structured reading notes on a given topic. This mode will integrate explanatory text with visuals like images, charts, or diagrams to aid understanding and memory. The output will be a document containing a combination of text and visuals, generated based on the provided context. If learning gaps are also provided, the output will include text explanations to address those specific gaps.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Topic/Concept, Grade Level, Curriculum/Exam Goal, Context). Output: A formatted text document with:
AI-curated notes with highlighted key terms, including a 5-minute summary, and integrated visuals (images, charts, or diagrams).
Annotations and a quick glossary of technical terms.
Memory hacks such as mnemonics, chunking, analogy mapping, and spaced repetition triggers.
Text explanations and key data points to be visualized for detected learning gaps.
AI-generated guidance on visual cues, patterns to aid memory, and a list of visual interpretation questions.
Acceptance Criteria: The output must be concise, accurate, and include all specified elements. The content should be adaptable to different grade levels and effectively represent complex relationships and data through text and visuals.
Feature 2: Learn by Writing (Descriptive & Analytical) 
Description: Generate questions that require students to write a response, such as explaining a topic in their own words or answering a specific question. This feature is for repetition purposes and helps determine if learning gaps are due to a lack of remembrance. It is used exclusively in After-hour mode.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Topic/Concept, Grade Level, Specific Writing Prompt, Context).
Output:
A detailed, open-ended writing prompt, including questions like "Explain in your own words what you learned about..." and topic-specific questions. The agent will generate a few questions for which students have to write short or long-type answers.
Acceptance Criteria: The prompt must be clear and open-ended. The questions should be designed to effectively assess both comprehension and recall.
Feature 3: Learn by Watching
Description: Find and suggest relevant YouTube videos based on the provided context and learning gaps. The agent will analyze the educational content of the videos and recommend them to provide a visual learning experience.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Topic/Concept, Context). Output: A list of curated YouTube video links, each with:
A brief summary of the video's content.
Acceptance Criteria: The suggested videos must be highly relevant to the topic and grade level. The explanation for each video must be clear and concise.
Feature 4: Learn by Playing
Description: The agent's role is to generate a game link URL based on a list of identified learning gaps. The games are created and hosted externally. The game link generation code will take a list of learning gaps and generate a URL that directs the user to an appropriate game. This feature can be used in both After-hour Session and Remediation modes to address specific learning gaps.
Input: Teacher Class ID, Duration, Learning Gaps, Learning Mode Specific Inputs (A list of detected learning gaps (e.g., ['historical_dates_gap', 'spelling_gap'])).
Output:
A single, fully formed game link URL.
Acceptance Criteria: The system must successfully call the game link generation code and return a functional URL. The generated URL must correspond to a game that addresses the provided learning gaps.
Feature 5: Learn by Doing
Description: Generate a hands-on exercise, experiment, or real-world task. This feature is mainly for homework but can also be used to solve gaps (very rarely). The tasks are practical, such as a small experiment to test the pH of soap using turmeric as an indicator.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Topic/Concept, Grade Level, Learning Objective).
Output: A step-by-step guide for a practical task, including:
Materials list.
Detailed instructions for the task or experiment.
Post-task scenario questions to test knowledge transfer.
Acceptance Criteria: The task must be safe, practical, and directly tied to the learning objective. The evaluation criteria should be specific and constructive.
Feature 6: Learning by Solving (Structured Problem-Solving)
Description: Generate a problem set with varying difficulty for subjects like math, grammar, or science. The problems will be created using context from in-class questions, scripts, and identified learning gaps to give students hands-on practice.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Subject, Topic, Grade Level, Number of Problems, Problem Type (MCQ, FITB, step-by-step), Context).
Output:
A problem set with progressive difficulty.
Automated scheduling logic to re-present problems on weak areas pinpointed in the previous context.
Acceptance Criteria: The problem set must be balanced in difficulty. The solutions must be clear and provide sufficient guidance without giving away the answer too early.
Feature 8: Learning by Questioning & Debating
Description: This agent's purpose is to create the complete debate setting, including the topic, personas, and prompts, by analyzing a student's context and identified gaps. This setting will then be used to initiate a dialogue with a live model.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Context).
Output: A detailed debate prompt and setting, including:
The debate settings (topic, format, and rules).
A simulated persona with a historically faithful, context-rich tone.
The AI's conversational prompts for the Socratic mode ("Why?", "What if?").
A concluding prompt for the user to summarize takeaways and link them to learning objectives.
Acceptance Criteria: The AI's dialogue must be engaging and encourage critical thinking. The persona's responses must be consistent and factually accurate.
Feature 9: Learning by Listening & Speaking
Description: Generate an audio-first content script, such as a podcast-style lecture or a story with characters. 
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Topic/Concept, Target Age, Desired Tone (e.g., "humorous," "informative")).
Output: A narrative script for an audio experience, including:
A conversational, age-appropriate script.
Relatable analogies and storytelling elements.
Verbal comprehension check questions.
Acceptance Criteria: The script must be well-paced and engaging for listening. The questions must be easy to answer verbally.
Note: checkout notebooklm
Feature 10: Learning by Assessment (Assessment Generation Agent)
Description: Generate a short assessment, such as a quiz or problem set, based on the content generated by the other modes. The goal is to test for any remaining learning gaps and ensure students have understood the content.
Input: Teacher Class ID, Duration, Learning Gaps (optional), Learning Mode Specific Inputs (Content Generated, Assessment Type (e.g., MCQ, short answer, true/false), Context).
Output: A structured set of assessment questions, including:
A clear set of questions of varying difficulty.
An answer key with explanations for each question.
A summary of the key concepts being tested.
Acceptance Criteria: The assessment questions must be directly relevant to the content and learning gaps addressed in the session. The questions should be clear, and the provided answers and explanations should be accurate and comprehensive.
6. Multi-Agent Orchestration Flow
The system will operate with a multi-agent architecture to manage content generation. A central orchestrator agent will receive all initial requests and distribute tasks to specialized mini-agents.
Request Reception: The orchestrator receives the user's request, including all standard inputs (Teacher Class ID, Duration, Learning Gaps, etc.) and the selected learning modes.
Task Delegation: Based on the selected composition of learning modes, the orchestrator calls the corresponding mini-agents (e.g., the Learn by Reading agent, the Learn by Playing agent).
Content Generation: Each mini-agent processes its specific task, generating the required content based on its own logic and the provided inputs.
Database Storage: The generated content from each mini-agent is stored in the database, linked to the Teacher Class ID for future reference and retrieval.
Output & Confirmation: Once all mini-agents have completed their tasks and the content has been successfully stored, the orchestrator returns a job ID or a status of completion to the user, confirming that the content has been successfully generated and is available in the database.
7. Assessment Model
The Assessment Model is a specialized mini-agent within the multi-agent system. Its primary function is to act as a final evaluation step after other content generation modes have been executed. The orchestrator calls this model as a final action to verify that the student has fully grasped the concepts and that any identified learning gaps have been successfully addressed.
This model is designed to be highly contextual. It uses the Learning Gaps and Context inputs from the orchestrator, which includes all previous sessions' data for the day. This allows it to generate an assessment that is not only relevant to the immediate session but also checks for knowledge retention and mastery over time. The output of this model is a set of assessment questions that will be stored in the database, just like the output of other content generation modes.
