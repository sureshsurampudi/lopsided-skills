---
name: story-writing
description: Project-specific enrichment of use-case-writing for implementation stories and design documents. Covers delegation syntax, variable styling, and JIRA/Confluence formatting. Read the use-case-writing skill first.
auto-activation: Writing implementation stories, designing story specifications, working with domain specific actions, story use cases.
---

# Story Writing

Prerequisite: read the [use-case-writing](../use-case-writing) skill first, then read the appropriate style file (`cockburn-style.md` or `pseudo-code-style.md`).

This document layers project-specific conventions on top.

## Delegation Syntax

Use cases in this project invoke actions via well-known patterns. Use the appropriate one for the context.

**Domain actions** (story specifications, flow designs):
```
Call domain specific action _loadOrder_; provide _orderId_ as input
```

**Service calls** (service/component designs):
```
Call _inventoryService.getResource_ with _resourceId_; call it _resourceData_
Call _activationService.createService_ with _activationRequest_; call it _createdService_
```

**HTTP endpoints** (REST API designs):
```
POST /notify/nestedOrderCompleted with body _callbackPayload_
GET /api/v4/resource?_resourceId_ ; call it _resourceData_
```

**Sub use cases** (any context):
```
Call use case _Validate Order_; provide _order_ as input
```

## Variable Styling

| Element | Style |
|---------|-------|
| Variables | _italics with underscores_ |
| Types/Classes | `backticks` |
| Field paths | _entity.field.subfield_ |
| Enum/string values | "quoted" |

## JIRA and Confluence Formatting

**Numbered Lists**: Use `1.` syntax (NOT `#`). In JIRA markup, `#` creates Heading 1.

```
_Main Success Scenario:_
1. First step
1. Second step with result; call it _namedResult_
```

**Line Breaks in Lists**: Trailing space at end of line:

```
1. Load item info; call it _itemInfo_
   Call domain action {{loadItemInfo}}; provide _orderId_
```

**Inline Code**: Use `{{monospace}}` in JIRA/Confluence instead of backticks.

**Before Upload Checklist**:

- [ ] All numbered lists use `1.` syntax
- [ ] No `#` used for list items
- [ ] Inline code uses `{{monospace}}`
- [ ] Multi-line list items use trailing space for line breaks
