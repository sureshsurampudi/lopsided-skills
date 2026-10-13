# Pseudo-Code Style

Use this style when the request mentions "pseudo-code", "BVR extraction", "validation rules", "condition-action", or explicit IF/THEN format.

This style produces a **linear, condition-first** specification — every path through the logic is spelled out inline using IF/THEN branches, with no separate extension section. Complex or deeply nested logic is extracted into named sub-flows.

## Overview — What Pseudo-Code Looks Like

```
## Rule

1. Extract the _product order_ from the request body; call it _payload_.
2. IF _payload.id_ is provided AND central ID generation is active; THEN
   Terminate — error _INVALID-ID-FORMAT_: "ID Format NOT valid for Order Id={id}"
3. IF _payload.id_ is provided AND a regex pattern is configured; THEN
   Validate _payload.id_ against the configured regex pattern.
   IF the ID does not match the regex; THEN
      Terminate — error _INVALID-ID-FORMAT_: "ID Format NOT valid for Order Id={id}"
```

---

## Structure

### 1. Markdown

**Do NOT use Markdown list syntax for numbered items.** Use manual prefix numbering inside the flow of text. This keeps formatting stable across all renderers.

Write the Rule section as plain paragraphs with manual numbering:

```
## Rule

1. Extract the _product order_ from the request body; call it _payload_.
2. IF _payload.state_ is "draft" or null; THEN skip all date validations.
3. IF _payload.requestedStartDate_ is provided; THEN
   Validate that _requestedStartDate_ + `maxLatency` hours is not before current time.
   IF the date is too far in the past; THEN
      Terminate — error _INVALID-START-DATE_: "Order must have a valid requestedStartDate"
```

**Indentation** is two spaces per nesting level. Use the same prefix numbering as the parent, with no additional numbering:

```
4. IF _requestedCompletionDate_ is provided; THEN
   Validate that _requestedCompletionDate_ is not too far in the past.
   IF the date is too far in the past; THEN
      Terminate — error _INVALID-COMPLETION-DATE_: "Check requestedCompletionDate"
```

### 2. Condition-Action Blocks

Every rule is a sequence of steps. Steps can be:

- **Unconditional actions** — plain sentences
- **Conditional branches** — IF/THEN blocks
- **Loops** — FOR EACH blocks
- **Delegations** — Call use case / Call service

Use IF/THEN with conditions on the same line:

```
IF _payload.id_ is provided AND _payload.id_ matches an existing record; THEN
   Terminate — error _DUPLICATE-ID_: "Entity with ID already exists."
```

For alternatives (if-else), use ELSE IF:

```
IF _resourceStatus_ equals "available"; THEN
   Prepare immediate allocation; call it _allocationResult_
ELSE IF _resourceStatus_ equals "reserved"; THEN
   Prepare reservation transfer; call it _allocationResult_
ELSE
   Prepare queue for next available; call it _allocationResult_
```

### 3. Construct Reference

| Construct | Format | Example |
|-----------|--------|---------|
| IF/THEN | `IF _condition_; THEN` | `IF _payload.id_ is null; THEN` |
| ELSE IF | `ELSE IF _condition_; THEN` | `ELSE IF _status_ is "reserved"; THEN` |
| ELSE | `ELSE` | `ELSE` |
| FOR EACH | `FOR EACH _item_ in _collection_:` | `FOR EACH _item_ in _payload.productOrderItem[]_:` |
| Terminate — error | `Terminate — error _CODE_: "message"` | `Terminate — error _DUPLICATE-ID_: "Entity already exists"` |
| Skip | `Skip this validation` | `Skip this validation (draft orders are exempt)` |
| Call use case | `Call use case _Name_; provide _input_` | `Call use case _Validate Order Item_; provide _item_` |

### 4. Nesting Constraint — Max 2 Levels

**Do NOT exceed 2 levels of IF nesting.** If logic requires deeper nesting, extract the inner logic into a named sub-flow.

**Example — too deep (3 levels):**
```
3. FOR EACH _item_ in _payload.items[]_:
   IF _item.product.isBundle_ is true; THEN
      IF _item.relationship[]_ is empty; THEN           ← level 2
         IF _item.productSpecification_ is null; THEN   ← level 3 — TOO DEEP
            Terminate — error _BUNDLE-INVALID_
```

**Fix — extract sub-flow:**
```
3. FOR EACH _item_ in _payload.items[]_:
   Call use case _Validate Bundle Item_; provide _item_
```

Then in a separate section or inlined at the same nesting level:

```
_Validate Bundle Item_:
IF _item.product.isBundle_ is true AND _item.relationship[]_ is empty; THEN
   IF _item.productSpecification_ is null; THEN
      Terminate — error _BUNDLE-INVALID_: "Missing product specification"
```

**Exception:** A flat FOR EACH with a 1-level IF inside is fine (total depth 2).

### 5. Sub-Flow Extraction Rules

Extract to a named sub-flow when:

1. **Nesting exceeds 2 levels** — as described above
2. **A validation block exceeds 6 steps** — more than 6 consecutive steps for a single sub-concern
3. **The logic is reused** — same condition appears in multiple BVRs or across endpoints
4. **The logic is semantically separable** — "item relationship validation" is a clear sub-concept within "order validation"

Sub-flows are documented inline as a named block:

```
...
Call use case _Validate Item Relationships_; provide _payload_

_Validate Item Relationships_:
1. FOR EACH _item_ in _payload.productOrderItem[]_:
   ...
```

Or as a separate section following the Rule section:

```
## Sub-Flows

### Validate Item Relationships
1. ...
```

### 6. Loops

```
FOR EACH _orderItem_ in _payload.productOrderItem[]_:
   Validate that _orderItem.action_ is not null.
   IF _orderItem.action_ is null; THEN
      Terminate — error _MISSING-ACTION_: "Item action is required"
```

For loops with index:

```
Loop from 0 to _count_ - 1 as _index_:
   Extract _item_ at index _index_ from _items_
   ...
```

### 7. Terminate — Error

Every termination point must be individually and locally labeled with an error code:

```
Terminate — error _INVALID-ID-FORMAT_: "ID Format NOT valid for Order Id={id}"
```

Error codes use UPPER_SNAKE_CASE with the format `_CODE_`. The message after the colon is the exact error message from the source.

---

## Constraints Summary

| Constraint | Rule |
|-----------|------|
| Nesting depth | Max 2 levels of IF |
| Sub-flow extraction | At depth 3, 6+ steps, or semantic separation |
| Numbering | Manual (non-list), not Markdown list syntax |
| Error labels | Every termination point must have `_CODE_` |
| Condition prefix | Conditions use `_variable_` names in italics |
| Line breaks | Use `<br>` or plain line breaks, never Markdown list continuation |

---

## Examples

### Simple IF/THEN

```
## Rule

1. Extract the _payload_ from the request body; call it _payload_.
2. IF _payload.id_ is null; THEN skip ID validation.
3. IF _payload.id_ matches an existing record; THEN
   Terminate — error _DUPLICATE-ID_: "Entity with ID already exists."
```

### IF/THEN with Sub-flow

```
## Rule

1. Extract the _product order_ from the request body; call it _payload_.
2. FOR EACH _item_ in _payload.productOrderItem[]_:
   Call use case _Validate Order Item_; provide _item_

## Sub-Flows

### Validate Order Item

1. IF _item.product_ is null; THEN
   Terminate — error _PRODUCT-REQUIRED_: "Product is mandatory for each order item."
2. IF _item.action_ is not a valid modification type; THEN
   Terminate — error _INVALID-ACTION_: "Unsupported action type."
```

### Complex Validation with Multiple Branches

```
## Rule

1. Extract the _product order_ from the request body; call it _payload_.
2. IF _payload.state_ is "draft" or null; THEN skip all date validations.
3. IF _payload.requestedStartDate_ is provided; THEN
   Validate that _requestedStartDate_ + configured latency is not before current time.
   IF the date is too far in the past; THEN
      Terminate — error _INVALID-START-DATE_: "Order must have a valid requestedStartDate"
4. IF _payload.requestedCompletionDate_ is provided; THEN
   Validate that _requestedCompletionDate_ + configured latency is not before current time.
   IF the date is too far in the past; THEN
      Terminate — error _INVALID-COMPLETION-DATE_: "Check requestedCompletionDate"
5. IF both dates are provided AND _requestedCompletionDate_ is before _requestedStartDate_; THEN
   Terminate — error _COMPLETION-BEFORE-START_: "requestedCompletionDate must be after requestedStartDate"
```
