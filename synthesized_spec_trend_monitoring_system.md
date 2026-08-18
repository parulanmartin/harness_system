# Engineering Specification & Requirements

## 1. Executive Summary & JTBD Matrix
| Actor | Situation (When...) | Motivation (I want to...) | Desired Outcome (So that...) |
|-------|----------------------|---------------------------|------------------------------|
| Nathan Jenk | When initiated by stakeholder | Mainstream tools act as lagging indicators because they measure volume after saturation. | Detect acceleration and velocity deltas in micro-communities. |
| Martin Parulan | When initiated by stakeholder | I want to get updated everytime I have new trends about businesses | Deliver actionable outcome to stakeholder |
| Martin Parulan | When initiated by stakeholder | It's hard to monitor multiple sources | Deliver actionable outcome to stakeholder |
| Martin Parulan | When initiated by stakeholder | Funneling all sources into one places | Deliver actionable outcome to stakeholder |
| Martin Parulan | When initiated by stakeholder | Finding the things to work on | Deliver actionable outcome to stakeholder |
| Martin Parulan | After calls | Don't have to asses everytime and it will be easy for us to monitor our updates | To make meeting information easily accessible and helpful. |
| User | When working in system | Mainstream tools act as lagging indicators, measuring volume after saturation. | Identify trends at the 'cultural edge' before mainstream media or aggregate platforms pick them up, providing an informational edge. |
| User | When initiated by stakeholder | Stakeholder approved standard workflow | Quantify and score signals based on acceleration rather than total volume. |
| User | When working in system | Monitoring micro-pools and specific, concentrated spaces is more effective than monitoring the 'big ocean'. | Ingest data from targeted, high-signal sources efficiently. |
| User | When initiated by stakeholder | Stakeholder approved standard workflow | Provide actionable insights by categorizing anomalous keyword spikes and highlighting consumer/tech shifts. |
| User | When initiated by stakeholder | Stakeholder approved standard workflow | Improve the accuracy of signal detection by reducing false positives from bot spikes and viral noise. |
| User | When initiated by stakeholder | Stakeholder approved standard workflow | Ensure the anomaly detection system works effectively across different types of niche communities. |

## 2. Functional & Non-Functional Requirements
- REQ-DETECT_EARLY_WEAK_TREND_SIGNALS: As a Nathan Jenk, I want to Detect early, weak trend signals across niche digital communities. so that Detect acceleration and velocity deltas in micro-communities..
- REQ-BUILD_SIGNAL_FILTERING_HARNESS: As a Martin Parulan, I want to Implement a velocity-delta scoring pipeline to separate genuine breakout chatter from inorganic bot spikes and one-off viral noise. so that Deliver actionable outcome to stakeholder.
- REQ-PROTOTYPE_NICHE_DATA_CONNECTORS: As a Martin Parulan, I want to Build scrapers/webhooks for 3–5 initial high-signal sources (e.g., specialized developer forums, niche beauty/fashion message boards, early consumer review boards). so that Deliver actionable outcome to stakeholder.
- REQ-WIRE_UP_LLM_SYNTHESIS_LAYER: As a Martin Parulan, I want to Wire up an automated daily digest that groups anomalous phrase spikes and synthesizes the underlying trends. so that Deliver actionable outcome to stakeholder.
- REQ-BUILD_TEST_HARNESS_FOR_NICHES: As a Martin Parulan, I want to Build a test harness for three distinct niches: developer tooling, niche consumer goods, and hobbyist hardware. so that Deliver actionable outcome to stakeholder.
- REQ-AUTOMATE_MEETING_SUMMARY_DUMP: As a Martin Parulan, I want to Automatically dump daily meeting summaries and screenshots into Google Docs after calls. so that To make meeting information easily accessible and helpful..
- REQ-G1: As a User, I want to Detect early, weak trend signals across niche digital communities. so that Identify trends at the 'cultural edge' before mainstream media or aggregate platforms pick them up, providing an informational edge..
- REQ-G2: As a User, I want to Implement a velocity-delta scoring pipeline to separate genuine breakout chatter from inorganic bot spikes and one-off viral noise. so that Quantify and score signals based on acceleration rather than total volume..
- REQ-G3: As a User, I want to Prototype niche data connectors for high-signal sources. so that Ingest data from targeted, high-signal sources efficiently..
- REQ-G4: As a User, I want to Wire up an automated daily digest that groups anomalous phrase spikes and synthesizes the underlying 'why' in 2 sentences. so that Provide actionable insights by categorizing anomalous keyword spikes and highlighting consumer/tech shifts..
- REQ-G5: As a User, I want to Refine the noise-filtering harness. so that Improve the accuracy of signal detection by reducing false positives from bot spikes and viral noise..
- REQ-G6: As a User, I want to Validate the anomaly model with 3 distinct niches. so that Ensure the anomaly detection system works effectively across different types of niche communities..
- NFR-QUANTIFIABLE_SIGNALS: System must adhere to constraint: 'Signals must be quantifiable using automated anomaly detection and LLM-powered root cause clustering.' (SLA: Automated anomaly detection and LLM-powered root cause clustering must be applied to all signals.).
- NFR-C1: System must adhere to constraint: 'A keyword must cross three standard deviations above its 14-day rolling average to be flagged yellow.' (SLA: 3 standard deviations above 14-day rolling average).
- NFR-C2: System must adhere to constraint: 'A flagged keyword must sustain its elevated state for over six hours to flip to red.' (SLA: sustained for >6 hours).
- NFR-C3: System must adhere to constraint: 'The automated daily digest must synthesize the underlying 'why' in 2 sentences.' (SLA: 2 sentences).
- NFR-C4: System must adhere to constraint: 'The system should monitor 50 high-signal, inconvenient sources rather than 5,000 generic ones.' (SLA: Number of high-signal sources vs. generic sources).

## 3. Data Entities
- **Trend Signal** (Fields: velocity-delta score, anomaly score, quantifiable, velocity deltas, keyword, mentions, acceleration): An indicator of an emerging trend, characterized by a significant rate of change in mentions within a niche community.
- **Niche Data Node**: Sources of information from micro-communities (e.g., Korean beauty forum, Discord bot logs, open-source dependencies).
- **Signal Filtering Harness** (Fields: rolling average, velocity-delta scoring pipeline, duration threshold, standard deviations): A system component designed to process raw data streams and identify genuine trend signals by filtering out noise.
- **Niche Data Connector**: Scrapers or webhooks for ingesting data from specific niche sources.
- **LLM Synthesis Layer** (Fields: underlying 'why', daily digest, vector embeddings, LLM batch jobs, anomalous phrase spikes): An AI-powered component that groups and interprets anomalous keyword spikes to synthesize actionable insights.
- **Daily Summary**: An automated digest of anomalous phrase spikes and underlying trends.
- **Meeting Summary**: A summary of meeting discussions and decisions.
- **Screenshot**: Visual captures related to meeting content.
- **Google Docs**: A platform for document storage and collaboration.
- **Core Domain Entity**: Core domain data entity.
- **Core Domain Entity**: Core domain data entity.
- **Core Domain Entity**: Core domain data entity.
- **Core Domain Entity**: Core domain data entity.
- **Core Domain Entity**: Core domain data entity.
- **Core Domain Entity**: Core domain data entity.
- **Niche Data Source** (Fields: type (e.g., forum, message board, repo), API/webhook, scraper): Specific, concentrated online communities or platforms where early trend signals are likely to emerge (e.g., Reddit, GitHub, Korean beauty forums, specialized developer forums).
- **Dashboard Prototype** (Fields: live feed, sparkline graphs, score visualization, alert triggers): A user interface for visualizing incoming signal streams and detected trends.

## 4. Acceptance Criteria & Edge Cases
```text
SCENARIO-DETECT_EARLY_WEAK_TREND_SIGNALS: Happy Path
  GIVEN Nathan Jenk is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Detect early, weak trend signals across niche digital communities.'
  THEN the system achieves: 'Detect acceleration and velocity deltas in micro-communities.'
```
```text
SCENARIO-DETECT_EARLY_WEAK_TREND_SIGNALS-ERR-1: Edge Case / Exception
  GIVEN Nathan Jenk encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-BUILD_SIGNAL_FILTERING_HARNESS: Happy Path
  GIVEN Martin Parulan is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Implement a velocity-delta scoring pipeline to separate genuine breakout chatter from inorganic bot spikes and one-off viral noise.'
  THEN the system achieves: 'Deliver actionable outcome to stakeholder'
```
```text
SCENARIO-BUILD_SIGNAL_FILTERING_HARNESS-ERR-1: Edge Case / Exception
  GIVEN Martin Parulan encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-PROTOTYPE_NICHE_DATA_CONNECTORS: Happy Path
  GIVEN Martin Parulan is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Build scrapers/webhooks for 3–5 initial high-signal sources (e.g., specialized developer forums, niche beauty/fashion message boards, early consumer review boards).'
  THEN the system achieves: 'Deliver actionable outcome to stakeholder'
```
```text
SCENARIO-PROTOTYPE_NICHE_DATA_CONNECTORS-ERR-1: Edge Case / Exception
  GIVEN Martin Parulan encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-WIRE_UP_LLM_SYNTHESIS_LAYER: Happy Path
  GIVEN Martin Parulan is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Wire up an automated daily digest that groups anomalous phrase spikes and synthesizes the underlying trends.'
  THEN the system achieves: 'Deliver actionable outcome to stakeholder'
```
```text
SCENARIO-WIRE_UP_LLM_SYNTHESIS_LAYER-ERR-1: Edge Case / Exception
  GIVEN Martin Parulan encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-BUILD_TEST_HARNESS_FOR_NICHES: Happy Path
  GIVEN Martin Parulan is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Build a test harness for three distinct niches: developer tooling, niche consumer goods, and hobbyist hardware.'
  THEN the system achieves: 'Deliver actionable outcome to stakeholder'
```
```text
SCENARIO-BUILD_TEST_HARNESS_FOR_NICHES-ERR-1: Edge Case / Exception
  GIVEN Martin Parulan encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-AUTOMATE_MEETING_SUMMARY_DUMP: Happy Path
  GIVEN Martin Parulan is in context: 'After calls'
  WHEN they perform: 'Automatically dump daily meeting summaries and screenshots into Google Docs after calls.'
  THEN the system achieves: 'To make meeting information easily accessible and helpful.'
```
```text
SCENARIO-AUTOMATE_MEETING_SUMMARY_DUMP-ERR-1: Edge Case / Exception
  GIVEN Martin Parulan encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G1: Happy Path
  GIVEN User is in context: 'Standard workflow'
  WHEN they perform: 'Detect early, weak trend signals across niche digital communities.'
  THEN the system achieves: 'Identify trends at the 'cultural edge' before mainstream media or aggregate platforms pick them up, providing an informational edge.'
```
```text
SCENARIO-G1-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Building 'yet another Google Trends clone''
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G2: Happy Path
  GIVEN User is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Implement a velocity-delta scoring pipeline to separate genuine breakout chatter from inorganic bot spikes and one-off viral noise.'
  THEN the system achieves: 'Quantify and score signals based on acceleration rather than total volume.'
```
```text
SCENARIO-G2-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G3: Happy Path
  GIVEN User is in context: 'Standard workflow'
  WHEN they perform: 'Prototype niche data connectors for high-signal sources.'
  THEN the system achieves: 'Ingest data from targeted, high-signal sources efficiently.'
```
```text
SCENARIO-G3-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Scraping everything blindly, leading to garbage noise and high cost'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G4: Happy Path
  GIVEN User is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Wire up an automated daily digest that groups anomalous phrase spikes and synthesizes the underlying 'why' in 2 sentences.'
  THEN the system achieves: 'Provide actionable insights by categorizing anomalous keyword spikes and highlighting consumer/tech shifts.'
```
```text
SCENARIO-G4-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G5: Happy Path
  GIVEN User is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Refine the noise-filtering harness.'
  THEN the system achieves: 'Improve the accuracy of signal detection by reducing false positives from bot spikes and viral noise.'
```
```text
SCENARIO-G5-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```
```text
SCENARIO-G6: Happy Path
  GIVEN User is in context: 'When initiated by stakeholder'
  WHEN they perform: 'Validate the anomaly model with 3 distinct niches.'
  THEN the system achieves: 'Ensure the anomaly detection system works effectively across different types of niche communities.'
```
```text
SCENARIO-G6-ERR-1: Edge Case / Exception
  GIVEN User encounters error condition: 'Handle standard system timeouts and log error alerts'
  THEN system should display appropriate error and prevent invalid state.
```