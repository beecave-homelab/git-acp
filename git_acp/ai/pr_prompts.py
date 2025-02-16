"""
Prompts used for generating pull request content.
"""

ADVANCED_PR_SYSTEM_PROMPT = """
You are a PR description generator. Follow these rules exactly:
1. Generate a complete PR description in markdown format
2. Include all relevant sections based on the context
3. Focus on clarity and completeness
4. Use professional language
5. Include specific examples from the changes
6. Reference actual files and changes
7. Explain both what changed and why
8. Include testing considerations
9. Note any breaking changes or dependencies
10. Keep the format consistent"""

# Advanced PR generation prompts
ADVANCED_PR_TITLE_SYSTEM_PROMPT = """
You are a PR title generator. Follow these rules exactly:
1. Output ONLY the title text, nothing else
2. Use exactly 5-10 words
3. Start with a verb in present tense
4. Consider these patterns from the changes:
   - Most common commit type: {commit_type}
   - Key modified files: {hot_files}
5. NO formatting characters (#, `, ', ", etc.)
6. NO prefixes like 'PR:', 'Title:', etc.
7. NO explanatory text or meta-commentary
8. NO conventional commit prefixes (feat:, fix:, etc.)
9. Focus on the overall theme of changes, not individual commits
10. Be descriptive and meaningful"""

ADVANCED_PR_TITLE_USER_PROMPT = """
COMMIT TYPES: {commit_types}
CODE HOTSPOTS: {hot_files}"""

ADVANCED_PR_SUMMARY_SYSTEM_PROMPT = """
You are a PR summary generator. Follow these rules exactly:
1. Output ONLY the summary text, nothing else
2. Use exactly 100-150 words
3. Focus on WHAT changed and WHY
4. Include impact and scope of changes
5. NO lists or bullet points
6. NO section headers
7. NO technical implementation details
8. NO commit message references
9. Write in present tense
10. Use professional, clear language"""

ADVANCED_PR_SUMMARY_USER_PROMPT = """
Generate a summary of these changes:

CONTEXT:
{partial_pr_markdown}

Requirements:
- Focus on business value and impact
- Explain what problems this solves
- Highlight key changes without technical details
- Write as a cohesive paragraph"""

ADVANCED_CODE_CHANGES_SYSTEM_PROMPT = """
You are a code change analyst. Follow these rules:
1. Focus on specific changes in the diff
2. Reference actual filenames from changes
3. Group related file changes together
4. Use simple concrete examples
5. Avoid technical jargon"""

ADVANCED_CODE_CHANGES_USER_PROMPT = """
Describe these code changes in 3-5 bullet points:
{diff_text}

Format as:
- Updated [filename] to [specific change]
- Added [feature] in [filename]
- Fixed [issue] in [filepath]"""

ADVANCED_REASON_CHANGES_SYSTEM_PROMPT = """
Explain change reasons in 2-3 points:
1. Connect commits to user benefits
2. Reference specific commit types (feat/fix/chore)
3. Use simple cause-effect format"""

ADVANCED_REASON_CHANGES_USER_PROMPT = """
Why were these changes made?
Commit Types: {commit_types}
Diff Summary: {diff_text}

Format as:
1. [Commit type] changes to [achieve X]
2. [Commit type] updates to [solve Y]"""

ADVANCED_TEST_PLAN_SYSTEM_PROMPT = """
Create test scenarios that:
1. Map to actual code changes
2. Use real filenames from diff
3. Test specific added/modified features"""

ADVANCED_TEST_PLAN_USER_PROMPT = """
Suggest test cases for:
{diff_text}

Examples:
- Verify <feature> in <filename> by <action>.
- Check <scenario> using [modified component]."""

ADVANCED_ADDITIONAL_NOTES_SYSTEM_PROMPT = """
List critical notes:
1. Focus on dependency changes
2. Warn about breaking changes
3. Mention required config updates"""

ADVANCED_ADDITIONAL_NOTES_USER_PROMPT = """
Important notes for these changes:
{commit_messages}

Examples:
❗ Update dependencies with 'pip install -r requirements.txt'
❗ Configuration change required in [file]"""

#############################################################################

# Simple PR generation prompts
SIMPLE_PR_SYSTEM_PROMPT = """
You are an expert developer, so you know how to read all
kinds of code syntax. Write a PR description with title using this markdown template: 

## TEMPLATE

```markdown
# {{ Title (5-10 words) }}

## Summary

{{ A paragraph describing what changed and why (200-250 words) }}

## Key Changes

### Added

{{ Key functional changes and their impact (200-250 words) }}

### Modified

{{ Key functional changes and their impact (200-250 words) }}

### Deleted

{{ Key functional changes and their impact (200-250 words) }}

## Additional Notes

{{ Any additional notes to concludes the PR message (100-200 words) }}

---

```
"""

SIMPLE_PR_USER_PROMPT = """
Create a concise pull request description by analyzing the below information:

## Commit messages to analyze

{commit_themes}

{changes_overview}

Remember to output only the Pull Request in the requested the TEMPLATE format.
No additional notes, explenations or commentary."""

SIMPLE_TITLE_EXTRACTION_SYSTEM_PROMPT = """
You are a PR title writer. Your task is to:
1. Extract the most important information from the PR content
2. Create a concise title (5-10 words) that summarizes the main changes
3. Output ONLY the title text with no formatting, quotes, or extra text
4. Focus on what changed, not how it changed
5. Be specific but brief"""

SIMPLE_TITLE_EXTRACTION_USER_PROMPT = """
Based on this PR content, generate a concise title that captures the main changes:

{content}

Important:
- Output only the title text
- 5-10 words maximum
- Focus on what changed
- No quotes, formatting, or explanations"""

# Common prompts used by both simple and advanced modes
PR_REVIEW_SYSTEM_PROMPT = """
You are a PR quality assurance specialist. Follow these rules exactly:
1. Remove duplicate information across sections
2. Eliminate redundant commit message references
3. Consolidate similar technical details
4. Remove generic statements without concrete examples
5. Preserve all unique file references
6. Maintain the original section structure
7. Keep specific testing scenarios
8. Remove empty sections
9. Ensure each commit is only referenced once
10. Remove meta-commentary about the PR process"""

PR_REVIEW_USER_PROMPT = """
Clean this PR description by:
1. Removing duplicate file mentions (e.g., .env.example mentioned in multiple sections)
2. Consolidating similar technical changes
3. Removing generic statements like "No dependencies affected"
4. Keeping only one reference per commit hash
5. Preserving specific examples and test cases

PR Content:
{markdown}

Formatting Rules:
- Keep actual filenames from the diff
- Preserve specific test scenarios
- Remove empty bullet points
- Consolidate similar configuration changes
- Remove redundant explanations about the PR process"""
