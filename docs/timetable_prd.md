Of course. Here is a comprehensive Product Requirements Document (PRD) for the PupilTeach Intelligent Timetable & Lesson Pairing System, designed to be used as context within an AI-powered editor like Cursor.

This PRD formalizes your proposed architecture, breaking it down into clear requirements, data models, and user flows that a development team (or an AI assistant) can use to build the feature.

-----

## Product Requirements Document: PupilTeach Intelligent Timetable & Lesson Pairing System

**Version:** 1.0
**Date:** June 25, 2025
**Author:** PupilTeach Product Team
**Status:** Scoping / In Development

### 1\. Introduction

This document outlines the requirements for the **Intelligent Timetable & Lesson Pairing System**, a core component of the PupilTeach platform. The primary challenge is to bridge the gap between a static, externally-provided weekly timetable (often in PDF format) and the dynamic, sequential nature of lesson plans.

The current process in many institutions involves manual data entry and a rigid link between a date and a lesson. This system breaks down when faced with holidays, unexpected cancellations, or other schedule disruptions. This feature will automate the ingestion of the master timetable and intelligently pair scheduled class slots with the correct, sequenced lesson plans, ensuring that academic progress is maintained seamlessly.

### 2\. Problem Statement

Teachers and administrators spend significant time manually transcribing timetable information into a digital format. Furthermore, when a class is cancelled (e.g., due to a holiday), the entire sequence of future lesson plans must be manually shifted, creating administrative overhead and potential for error.

Our system needs to:

1.  Automate the digitization of weekly timetables provided in PDF format.
2.  Create a flexible link between a scheduled time slot and the actual lesson content.
3.  Ensure that lesson plans flow sequentially, automatically skipping non-teaching days (holidays, cancelled classes) without requiring manual rescheduling of every future lesson.

### 3\. Goals and Objectives

  * **Primary Goal:** To create a fully automated, resilient system that populates the `timetable_events` database from a source PDF and dynamically assigns the correct lesson to each class slot.
  * **Key Objectives:**
      * **Drastically Reduce Admin Work:** Eliminate manual data entry for weekly schedules.
      * **Improve Planning Resilience:** Ensure lesson continuity by automatically handling schedule gaps like holidays.
      * **Enable Proactive Planning:** Provide teachers with a clear, forward-looking view of their schedule, prepopulated with the appropriate lesson plans.
      * **Create Foundational Data:** Establish the core `timetable_event` entries that power all other PupilTeach features (lesson planning, in-class interaction, reporting).

### 4\. User Personas

  * **School Administrator:** Responsible for uploading the official weekly timetable PDF for the entire institution. They are the trigger for the ingestion process.
  * **Teacher:** The primary consumer of the feature. They view their daily/weekly schedule in PupilTeach, expecting to see the correct lesson plan attached to each class session.
  * **System (PupilTeach Backend):** The automated engine that performs the parsing, mapping, and pairing logic.

### 5\. Core Feature: The Timetable Ingestion & Pairing Engine

#### 5.1. Part A: Timetable PDF Ingestion

This module is responsible for parsing the uploaded timetable PDF and creating placeholder event slots in the database.

  * **Trigger:** A School Administrator uploads a new weekly timetable PDF via the PupilTeach admin portal.
  * **Process:**
    1.  The backend receives the PDF.
    2.  The PDF is sent to a **Gemini API endpoint** with a specialized prompt designed for structured data extraction from tabular documents.
    3.  The API returns a structured JSON object representing the timetable data.
    4.  The system validates and processes this JSON to create database entries.
  * **Gemini API Prompt Strategy:** The prompt should instruct the model to act as a data extraction tool and return a clean JSON array.
    > **Example Prompt:** "You are a data extraction service. Parse the following school timetable PDF and convert it into a JSON array. Each object in the array should represent a single class session and have the following keys: `dayOfWeek` (e.g., 'Monday'), `startTime` (e.g., '09:00'), `endTime` (e.g., '09:50'), `className` (e.g., 'Grade 10 Physics'), `teacherName` (e.g., 'Mr. A. Sharma'). Ignore empty cells and assembly periods. Calculate the duration based on start and end times."
  * **Data Mapping & Validation:**
      * Upon receiving the JSON, the system must map the string names (`className`, `teacherName`) to their corresponding `ObjectId`s in the `classes` and `users` (teachers) collections.
      * **Ambiguity Handling:** If a name is not found or is ambiguous (e.g., two teachers named 'A. Sharma'), the system will flag this entry for manual review by the administrator.
  * **Slot Creation:** For each successfully mapped entry, a new document is created in the `timetable_events` collection.
      * `scheduled_date` will be calculated based on the `dayOfWeek` and the week the timetable applies to.
      * `planned_lesson_id` will be set to `null` initially.
      * `status` will be set to `"scheduled"`.
      * `is_holiday` will be checked against a separate `holidays` collection. If the date is a holiday, this flag is set to `true`, and no lesson will be paired with it.

#### 5.2. Part B: The Lesson Pairing Logic

This is a recurring background process that fills the empty slots created in Part A.

  * **Trigger:** This process runs automatically after a new timetable is ingested and can also be run periodically (e.g., nightly) to handle any changes.
  * **Pre-requisite:** The `lessons` collection contains an ordered sequence of lessons for each class, defined by a `sequence_number` or similar field. A teacher would have already planned these lessons (e.g., "Chapter 1, Part 1", "Chapter 1, Part 2", etc.).
  * **The Logic:**
    1.  The system identifies a `class_id` that has timetable events with `planned_lesson_id: null`.
    2.  It fetches all `timetable_events` for that `class_id` that are `"scheduled"`, `is_holiday: false`, and have a `null` lesson ID, sorting them by `scheduled_date` in ascending order.
    3.  It fetches all `lessons` for the same `class_id` that have not yet been assigned to a timetable event (e.g., `status: 'draft'` or `'pending'`), sorting them by `sequence_number`.
    4.  The system iterates through the sorted timetable slots and assigns the `_id` of the next available lesson to the `planned_lesson_id` field.
    5.  It updates the status of the `lesson` to `"scheduled"` and links it back to the `timetable_event_id`.
  * **Handling Disruptions (The Core Value):** If the pairing logic encounters a `timetable_event` where `is_holiday` is `true` or `status` is `'cancelled'`, it simply **skips that slot**. The lesson queue is unaffected. The next lesson in the sequence will be assigned to the next available, valid class slot. This elegantly solves the manual rescheduling problem.

### 6\. Data Models (MongoDB Schemas)

#### `timetable_events` Collection

```json
{
    "_id": ObjectId("event_..."),
    "class_id": ObjectId("class_..."), // Ref to 'classes' collection
    "teacher_id": ObjectId("user_teacher_..."), // Ref to 'users' collection
    "scheduled_date": ISODate("2025-09-15T09:00:00Z"), // Start time of the event
    "duration_minutes": 50,
    "event_type": "class_session", // Enum: ['class_session', 'holiday', 'exam', 'admin_task']
    "planned_lesson_id": ObjectId("lesson_..."), // Ref to 'lessons' collection. Null initially.
    "status": "scheduled", // Enum: ['scheduled', 'completed', 'cancelled', 'rescheduled']
    "is_holiday": false,
    "rescheduled_to_event_id": null, // Ref to another event if rescheduled
    "ingestion_batch_id": ObjectId("batch_..."), // To track which upload this came from
    "createdAt": ISODate(),
    "updatedAt": ISODate()
}
```

#### `lessons` Collection (Assumed Pre-requisite)

This collection is populated by the teacher's planning activities.

```json
{
    "_id": ObjectId("lesson_..."),
    "chapter_id": ObjectId("chapter_..."),
    "class_id": ObjectId("class_..."),
    "teacher_id": ObjectId("user_teacher_..."),
    "lesson_title": "Introduction to Newton's First Law",
    "sequence_number": 1, // Critical for the pairing logic
    "teleprompter_script": "...", // The AI-generated and refined script
    "status": "draft", // Enum: ['draft', 'scheduled', 'completed']
    "associated_timetable_event_id": null, // Link back to the event once paired
    "createdAt": ISODate(),
    "updatedAt": ISODate()
}
```

### 7\. Non-Functional Requirements

  * **Accuracy:** The PDF-to-JSON parsing must have a very high accuracy rate (\>98%). A manual correction interface is required for the administrator to resolve any flagged errors from the ingestion process.
  * **Performance:** Ingestion of a full-school timetable PDF should be processed and reflected in the database within 5 minutes.
  * **Scalability:** The system must handle timetables for institutions with up to 200 teachers and 50 classes without a degradation in performance.
  * **Error Handling:** The system must provide clear, actionable error logs to the administrator if ingestion or pairing fails (e.g., "Teacher 'R. Kumar' not found in database").

### 8\. Success Metrics

  * **Time to Publish:** Time saved by administrators (measured by reduction in time from receiving PDF to the schedule being live for teachers).
  * **Parsing Accuracy:** Percentage of timetable slots correctly parsed and mapped without manual intervention.
  * **Error Rate:** Number of scheduling conflicts or incorrect lesson pairings reported by teachers per week.
  * **User Satisfaction:** Qualitative feedback from teachers on the clarity and reliability of their auto-populated schedules.