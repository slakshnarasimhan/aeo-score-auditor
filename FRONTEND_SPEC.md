# AEO Score Auditor - Frontend Specification

## Overview
Complete UI/UX specification for the AEO Score Auditor dashboard with detailed component designs, user flows, and interaction patterns.

---

## APPLICATION STRUCTURE

```
AEO Score Auditor Dashboard
│
├── Authentication
│   ├── Login
│   └── API Key Management
│
├── Main Dashboard
│   ├── Quick Audit Form
│   ├── Recent Audits
│   └── Domain Overview Cards
│
├── Domain Dashboard
│   ├── Domain Overview
│   ├── Page Leaderboard
│   ├── Score Trends
│   └── Bulk Actions
│
├── Page Detail View
│   ├── Score Overview
│   ├── Score Breakdown
│   ├── Recommendations Panel
│   ├── Evidence Explorer
│   └── Historical Comparison
│
├── Recommendations Hub
│   ├── Recommendation List
│   ├── Quick Wins
│   ├── Implementation Tracker
│   └── Impact Analytics
│
└── Settings
    ├── Domain Management
    ├── Audit Scheduling
    └── Notifications
```

---

## 1. MAIN DASHBOARD

### 1.1 Quick Audit Form

**Location**: Top of main dashboard

**Components**:
```
┌─────────────────────────────────────────────────────────────┐
│  Audit a Page                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Enter URL: https://                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  [✓] Include AI Citation Analysis (adds 2-3 minutes)       │
│                                                             │
│  ┌──────────────┐                                          │
│  │ Audit Now    │   or  [Schedule for later]              │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Real-time URL validation
- Option toggle for AI citation
- Estimated time display
- Progress indicator after submission

**Interaction Flow**:
1. User enters URL
2. System validates URL (real-time)
3. User clicks "Audit Now"
4. Modal appears showing progress
5. Redirect to results when complete

---

### 1.2 Recent Audits

**Location**: Below quick audit form

**Layout**:
```
Recent Audits                                    [View All]

┌────────────────────────────────────────────────────────────┐
│ example.com/blog/aeo-guide          Score: 78.5 (B+)      │
│ 2 hours ago                         ↑ +3.2 from last      │
│ [View Details] [Re-audit]                                  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ example.com/guides/seo              Score: 82.0 (A-)       │
│ 1 day ago                           ↑ +5.0 from last       │
│ [View Details] [Re-audit]                                  │
└────────────────────────────────────────────────────────────┘
```

**Data Displayed**:
- URL (truncated, with tooltip for full)
- Score with grade
- Time since audit
- Score change indicator
- Quick actions

---

### 1.3 Domain Overview Cards

**Location**: Below recent audits

**Layout**:
```
Your Domains                                     [+ Add Domain]

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ example.com      │ │ blog.acme.org    │ │ mysite.net       │
│                  │ │                  │ │                  │
│ Avg Score: 76.3  │ │ Avg Score: 68.5  │ │ Avg Score: 85.2  │
│ Grade: B+        │ │ Grade: C+        │ │ Grade: A         │
│                  │ │                  │ │                  │
│ 45 pages         │ │ 12 pages         │ │ 28 pages         │
│ Last: 2 hrs ago  │ │ Last: 3 days ago │ │ Last: 1 day ago  │
│                  │ │                  │ │                  │
│ [View Dashboard] │ │ [View Dashboard] │ │ [View Dashboard] │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Features**:
- Card-based layout (grid, 3 columns)
- Color-coded by grade (A=green, B=blue, C=yellow, D/F=red)
- Click card to open domain dashboard
- Quick stats visible

---

## 2. DOMAIN DASHBOARD

### 2.1 Domain Overview Header

**Location**: Top of domain dashboard page

```
┌─────────────────────────────────────────────────────────────┐
│ example.com                               [⚙ Settings] [↻]  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Avg Score   │  │ Total Pages │  │ Last Audit  │        │
│  │   76.3      │  │     45      │  │  2 hrs ago  │        │
│  │   Grade: B+ │  │             │  │             │        │
│  │  ↑ +2.5     │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│  Score Distribution:                                         │
│  [████████] A (5 pages)                                     │
│  [████████████████████████] B (25 pages)                    │
│  [████████████] C (10 pages)                                │
│  [████] D (3 pages)                                         │
│  [██] F (2 pages)                                           │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Key metrics in cards
- Trend indicators
- Visual score distribution
- Quick actions (settings, refresh)

---

### 2.2 Score Trends Chart

**Location**: Below domain overview

```
Score Trend (Last 30 Days)                    [30D] [90D] [1Y]

80 ┤                                    ●
   │                               ●         
75 ┤                          ●               
   │                     ●                    
70 ┤                ●                         
   │           ●                              
65 ┤      ●                                   
   │ ●                                        
60 ┤                                          
   └────────────────────────────────────────
    Nov 1        Nov 15        Nov 26

[Line shows: Avg Score] [Toggle: Show individual pages]
```

**Features**:
- Time range selector
- Interactive hover (show exact score)
- Toggle between average and individual pages
- Highlight major improvements/regressions

---

### 2.3 Page Leaderboard

**Location**: Below score trends

```
All Pages                          [Sort: Score ▼] [Filter ▾]

┌─────────────────────────────────────────────────────────────┐
│ Rank │ Page                      │ Score  │ Grade │ Actions │
├──────┼───────────────────────────┼────────┼───────┼─────────┤
│  1   │ /guides/complete-aeo      │  92.5  │  A+   │ [View]  │
│  2   │ /blog/optimization        │  88.0  │  A    │ [View]  │
│  3   │ /resources/tools          │  85.2  │  A    │ [View]  │
│  4   │ /blog/getting-started     │  82.0  │  A-   │ [View]  │
│  5   │ /guides/schema-basics     │  78.5  │  B+   │ [View]  │
│  ... │                           │        │       │         │
│ 43   │ /old-post-2020            │  45.0  │  F    │ [View]  │
└─────────────────────────────────────────────────────────────┘

Showing 1-20 of 45                         [1] [2] [3] [Next]
```

**Features**:
- Sortable columns
- Filter by score range, grade, category
- Pagination
- Bulk select for batch actions
- Color-coded grades

---

### 2.4 Bottom Pages (Quick Fixes)

**Location**: Right sidebar or below leaderboard

```
Pages Needing Attention

┌─────────────────────────────────────────────┐
│ /old-post-2020               Score: 45.0    │
│ Critical issues: 3           [Fix Now]      │
│ Quick wins available: 2                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ /blog/draft-content          Score: 52.0    │
│ Critical issues: 2           [Fix Now]      │
│ Quick wins available: 4                     │
└─────────────────────────────────────────────┘
```

---

## 3. PAGE DETAIL VIEW

### 3.1 Score Overview Card

**Location**: Top of page detail view

```
┌─────────────────────────────────────────────────────────────┐
│ example.com/blog/aeo-guide                                   │
│ Audited: 2 hours ago                    [Re-audit] [Export] │
│                                                              │
│         ┌──────────────┐                                     │
│         │              │                                     │
│         │    78.5      │      Grade: B+                     │
│         │              │                                     │
│         └──────────────┘                                     │
│           Overall AEO Score                                  │
│                                                              │
│  Previous: 75.3 (↑ +3.2)        Target: 85.0 (A-)          │
│                                                              │
│  12 recommendations available                                │
│  Potential gain: +18.5 points                               │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Large, prominent score
- Grade badge
- Comparison with previous
- Target score suggestion
- Quick actions

---

### 3.2 Score Breakdown

**Location**: Below score overview

```
Score Breakdown

┌─────────────────────────────────────────────────────────────┐
│ Answerability                            24/30 (80%)   [▼]  │
│ ████████████████████░░░░                                    │
│ › Direct Answer Presence: 10/12                             │
│ › Question Coverage: 6/8                                    │
│ › Answer Conciseness: 5/6                                   │
│ › Answer Block Formatting: 3/4                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Structured Data                          14/20 (70%)   [▼]  │
│ ██████████████░░░░░░                                        │
│ › JSON-LD Presence: 6/8                                     │
│ › Schema Type Relevance: 4/6                                │
│ › FAQ Schema Quality: 3/4                                   │
│ › Completeness: 1/2                                         │
└─────────────────────────────────────────────────────────────┘

[... more categories ...]
```

**Features**:
- Expandable/collapsible sections
- Visual progress bars
- Sub-score breakdown
- Color coding (green=good, yellow=needs work, red=critical)
- Click to see recommendations for that category

---

### 3.3 Recommendations Panel

**Location**: Right sidebar or tabbed view

```
Recommendations                          [Sort: Priority] [▾]

Quick Wins (2-3)
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Add TL;DR Summary Block                                  │
│ Priority: 85/100 | Impact: +6.0 pts | Time: 15 min         │
│ [View Details] [Mark as Done]                               │
└─────────────────────────────────────────────────────────────┘

High Impact (3)
┌─────────────────────────────────────────────────────────────┐
│ 🎯 Implement FAQPage Schema                                 │
│ Priority: 90/100 | Impact: +8.0 pts | Time: 20 min         │
│ [View Details] [Mark as Done]                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🎯 Add Article Schema with Author                           │
│ Priority: 88/100 | Impact: +7.0 pts | Time: 15 min         │
│ [View Details] [Mark as Done]                               │
└─────────────────────────────────────────────────────────────┘

Medium Priority (7)
[Collapsed by default]
```

**Features**:
- Grouped by priority/impact
- Visual priority indicators
- Estimated time
- Potential score gain
- Quick actions
- Collapsible sections

---

### 3.4 Recommendation Detail Modal

**Triggered**: Click "View Details" on recommendation

```
┌─────────────────────────────────────────────────────────────┐
│ Add TL;DR Summary Block                           [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Priority: 85/100  │  Impact: +6.0 pts  │  Effort: Easy     │
│                                                              │
│ Description:                                                 │
│ Add a TL;DR (Too Long; Didn't Read) summary at the top of   │
│ your article to provide a scannable summary.                │
│                                                              │
│ Why This Matters:                                            │
│ A TL;DR provides a concise summary that AI engines can      │
│ easily extract and cite...                                  │
│                                                              │
│ How to Fix:                                                  │
│  1. Write a 2-4 sentence summary of your main points        │
│  2. Place it prominently near the top                       │
│  3. Use visual formatting to make it stand out              │
│                                                              │
│ [Code Example] [Before/After] [Resources]                   │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ <div class="tldr-box">                                 │  │
│ │   <h2>TL;DR</h2>                                       │  │
│ │   <p><strong>Key Points:</strong></p>                  │  │
│ │   <ul>                                                 │  │
│ │     <li>Main takeaway #1</li>                          │  │
│ │   </ul>                                                │  │
│ │ </div>                                                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                [Copy Code]                   │
│                                                              │
│ Estimated Time: 15 minutes                                   │
│                                                              │
│ [Mark as Implemented] [Schedule for Later]                  │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Detailed explanation
- Step-by-step instructions
- Code snippets with copy button
- Before/after examples
- Resource links
- Implementation tracking

---

### 3.5 Evidence Explorer

**Location**: Separate tab on page detail view

```
AI Citation Evidence

┌─────────────────────────────────────────────────────────────┐
│ Queries: 60  │  Citations: 9  │  Citation Rate: 15%        │
└─────────────────────────────────────────────────────────────┘

By Engine:
┌──────────────┬───────────┬───────────┬──────────────┐
│ Engine       │ Queries   │ Citations │ Rate         │
├──────────────┼───────────┼───────────┼──────────────┤
│ Perplexity   │    20     │     7     │    35%       │
│ GPT-4        │    20     │     1     │     5%       │
│ Gemini       │    20     │     1     │     5%       │
└──────────────┴───────────┴───────────┴──────────────┘

Evidence Details:

┌─────────────────────────────────────────────────────────────┐
│ Perplexity | "What is AEO?"                        ✓ Cited  │
│                                                              │
│ Response:                                                    │
│ "Answer Engine Optimization (AEO) is the practice of        │
│ optimizing content to appear in AI-powered answer            │
│ engines..." [Source: example.com/blog/aeo-guide]            │
│                                                              │
│ Citation Type: URL mention                                   │
│ Semantic Similarity: 0.85                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ GPT-4 | "How does AEO work?"                      ✗ No cite │
│                                                              │
│ Response:                                                    │
│ "AEO involves structuring content with clear answers..."     │
│                                                              │
│ Semantic Similarity: 0.72                                    │
│ Fact Usage: 3 facts from page                               │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Summary statistics
- Engine-by-engine breakdown
- Detailed evidence cards
- Citation highlighting
- Similarity scores
- Filter by engine, cited/not cited

---

## 4. RECOMMENDATIONS HUB

### 4.1 Implementation Tracker

**Location**: Main recommendations page

```
Implementation Progress

Overall: 8/25 recommendations implemented (32%)
Potential gain remaining: +42.5 points

┌─────────────────────────────────────────────────────────────┐
│ Status          │ Count │ Potential Gain                    │
├─────────────────┼───────┼──────────────────────────────────┤
│ ✓ Implemented   │   8   │ +15.5 pts (actual: +12.3)        │
│ ⏳ In Progress  │   3   │ +8.0 pts                          │
│ 📋 Planned      │   5   │ +12.0 pts                         │
│ ⭕ Not Started  │   9   │ +22.5 pts                         │
└─────────────────────────────────────────────────────────────┘

Recent Implementations:

┌─────────────────────────────────────────────────────────────┐
│ ✓ Added FAQPage Schema                                      │
│ example.com/blog/aeo-guide                                   │
│ Implemented: 2 days ago                                      │
│ Expected: +8.0 pts | Actual: +6.5 pts                       │
│ [View Impact]                                                │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Progress overview
- Status tracking
- Impact measurement
- Implementation timeline

---

## 5. RESPONSIVE DESIGN

### Mobile Layout Adjustments

**Main Dashboard**:
- Stack cards vertically
- Simplified audit form
- Collapsible sections

**Domain Dashboard**:
- Tab-based navigation (Overview | Pages | Trends)
- Horizontal scroll for tables
- Condensed metrics

**Page Detail**:
- Tabbed interface (Score | Recommendations | Evidence)
- Collapsible score breakdown
- Bottom sheet for recommendation details

---

## 6. DESIGN SYSTEM

### Color Palette

```
Grades:
- A+/A:  #10b981 (green-500)
- A-/B+: #3b82f6 (blue-500)
- B/B-:  #6366f1 (indigo-500)
- C+/C:  #f59e0b (amber-500)
- C-/D:  #ef4444 (red-500)
- F:     #991b1b (red-900)

UI:
- Primary:    #6366f1 (indigo-500)
- Secondary:  #8b5cf6 (purple-500)
- Success:    #10b981 (green-500)
- Warning:    #f59e0b (amber-500)
- Error:      #ef4444 (red-500)
- Background: #f9fafb (gray-50)
- Card:       #ffffff (white)
- Border:     #e5e7eb (gray-200)
```

### Typography

```
- Headings: Inter, sans-serif
  - H1: 2.5rem, bold
  - H2: 2rem, semibold
  - H3: 1.5rem, semibold

- Body: Inter, sans-serif
  - Large: 1.125rem
  - Regular: 1rem
  - Small: 0.875rem

- Code: 'Monaco', 'Courier New', monospace
  - Regular: 0.875rem
```

### Spacing

```
- xs:  0.25rem (4px)
- sm:  0.5rem (8px)
- md:  1rem (16px)
- lg:  1.5rem (24px)
- xl:  2rem (32px)
- 2xl: 3rem (48px)
```

---

## 7. COMPONENT LIBRARY

### ScoreCircle Component

```jsx
<ScoreCircle 
  score={78.5} 
  grade="B+" 
  size="large"
  showChange={true}
  previousScore={75.3}
/>
```

### ScoreBar Component

```jsx
<ScoreBar 
  label="Answerability"
  score={24}
  maxScore={30}
  color="blue"
  expandable={true}
/>
```

### RecommendationCard Component

```jsx
<RecommendationCard 
  title="Add TL;DR Summary Block"
  priority={85}
  impact={6.0}
  effort="Easy"
  time="15 minutes"
  onView={handleView}
  onImplement={handleImplement}
/>
```

### EvidenceCard Component

```jsx
<EvidenceCard 
  engine="Perplexity"
  prompt="What is AEO?"
  response="..."
  cited={true}
  similarity={0.85}
/>
```

---

## 8. USER FLOWS

### Flow 1: First-Time Audit

```
1. User lands on dashboard
2. Enters URL in quick audit form
3. Clicks "Audit Now"
4. Progress modal shows steps:
   - Fetching page...
   - Extracting content...
   - Computing scores...
   - Evaluating AI citations...
   - Generating recommendations...
5. Redirect to page detail view
6. Show tour highlights:
   - Overall score
   - Score breakdown
   - Top recommendations
```

### Flow 2: Implementing Recommendation

```
1. User views page detail
2. Scrolls to recommendations panel
3. Clicks "View Details" on recommendation
4. Modal opens with full details
5. Copies code snippet
6. Implements on their site
7. Returns to AEO dashboard
8. Clicks "Mark as Implemented"
9. System prompts: "Re-audit to measure impact?"
10. User clicks "Yes"
11. New audit runs
12. Score improves, shows before/after
```

### Flow 3: Domain Monitoring

```
1. User adds domain
2. Sets audit schedule (weekly)
3. First audit runs, analyzes 50 pages
4. Weekly email: "Your AEO score changed"
5. User clicks link to domain dashboard
6. Views trend chart showing improvement
7. Identifies 3 pages needing attention
8. Drills into lowest-scoring page
9. Implements quick wins
10. Tracks progress over time
```

---

## 9. ACCESSIBILITY

### Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatible
- High contrast mode
- Focus indicators
- ARIA labels on all interactive elements
- Alt text for all images
- Semantic HTML

### Key Patterns

```html
<!-- Score card with ARIA -->
<div role="region" aria-labelledby="score-heading">
  <h2 id="score-heading">Overall AEO Score</h2>
  <div aria-live="polite" aria-atomic="true">
    <span class="score">78.5</span>
    <span class="grade">B+</span>
  </div>
</div>

<!-- Recommendation with keyboard support -->
<button 
  aria-label="View details for Add TL;DR Summary Block recommendation"
  onclick="showDetails()"
  onkeypress="handleKeyPress(event)"
>
  View Details
</button>
```

---

## 10. LOADING STATES

### Audit in Progress

```
┌─────────────────────────────────────────────────────────────┐
│ Auditing example.com/page...                                 │
│                                                              │
│ ✓ Fetching page                                             │
│ ✓ Extracting content                                        │
│ ⏳ Computing scores (45%)                                    │
│ ⭕ Evaluating AI citations                                   │
│ ⭕ Generating recommendations                                │
│                                                              │
│ Estimated time remaining: 2 minutes                          │
│                                                              │
│ [████████████░░░░░░░░░░] 60%                                │
└─────────────────────────────────────────────────────────────┘
```

### Skeleton Screens

```
┌─────────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░                                    │
│                                                              │
│ ░░░░░░░░  ░░░░░░░  ░░░░░░░░░                               │
│                                                              │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░         │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. ANIMATIONS & TRANSITIONS

### Micro-interactions

```css
/* Score animation on load */
@keyframes scoreReveal {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.score-circle {
  animation: scoreReveal 0.5s ease-out;
}

/* Progress bar fill */
@keyframes fillProgress {
  from { width: 0%; }
  to { width: var(--progress); }
}

.progress-bar {
  animation: fillProgress 0.8s ease-out;
}

/* Card hover effect */
.recommendation-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.recommendation-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}
```

---

## 12. TECH STACK RECOMMENDATION

### Frontend Framework
- **React** (v18+) with TypeScript
- **Next.js** for SSR/SSG
- **TailwindCSS** for styling

### State Management
- **React Query** for server state
- **Zustand** or **Context API** for client state

### Charts & Visualization
- **Recharts** or **Chart.js**
- **D3.js** for custom visualizations

### UI Components
- **Radix UI** or **Headless UI** for unstyled primitives
- **Framer Motion** for animations
- **React Hook Form** for forms

### Code Display
- **Prism** or **Highlight.js** for syntax highlighting
- **React Syntax Highlighter**

---

## NEXT STEPS
- MVP Roadmap with implementation timeline
- Starter code generation
- Component library setup

