---
name: use-case-writing
description: Alistair Cockburn use-case format — structure, tree model, extension numbering, result binding, and natural language patterns.
auto-activation: Writing use cases, main success scenarios, extension scenarios, Cockburn format, result binding, extension numbering, use case trees, sub use cases, BVR extraction, validation rules, pseudo-code, IF THEN conditions, business validation rules, specification by example.
---

# Use Case Writing

This skill supports two output styles. **Read the appropriate style file** based on the request:

- **Cockburn style** (default): Main scenario + extension tree. Read `cockburn-style.md`.
- **Pseudo-code style**: Linear IF/THEN with sub-flow extraction. Read `pseudo-code-style.md`. Use when the request mentions "pseudo-code", "BVR extraction", "validation rules", "condition-action", "IF/THEN", or "business rule specification".

If the user doesn't specify, use Cockburn style (read `cockburn-style.md`).

---

## Shared Conventions

These apply to BOTH styles.

### 1. Result Binding

Every operation that produces a result you'll use later gets a name:

```
Find the document with _id_; call it _idGenerationSpec_
Parse _lastIndexString_ as decimal; call the result _startIndex_
Calculate the changed fields; call it _deltaEntity_
```

### 2. Variable Styling

| Element | Style |
|---------|-------|
| Variables | _italics with underscores_ |
| Types/Classes | `backticks` |
| Field paths | _entity.field.subfield_ |
| Enum/string values | "quoted" |

### 3. Delegation Syntax

Delegation syntax varies by context. The generic form is:

```
Call use case _Validate Order_; provide _order_ as input
```

Context-specific forms enrich this with concrete action types:
- HTTP: `POST /orders with body _payload_; call it _createdOrder_`
- Service method: `Call _inventoryService.getResource_ with _id_; call it _resource_`

See your project's story-writing conventions for the specific delegates used in your context.

### 4. Inline Guidance

```
_NOTE:_ Clarification or rationale for the step.
**IMPORTANT:** Critical point that must not be missed.
Hint: Implementation suggestion (not a requirement).
```

### 5. Supplemental Data

Reference complex mappings, validation rules, or tables:

```
3. Convert _cart_ to _ProductOrderCreate_ according to mapping rules below; call it _order_
```

Then after the scenario:

```
**Supplemental Information**

_Cart to Order Mapping_

| Source Field | Target Field |
|--------------|--------------|
| cart.item[].product | order.orderItem[].product |
```

### 6. Context-Appropriate Outputs

| Context | Output Style |
|---------|-------------|
| REST endpoint | Implicit — omit _Outputs_ section |
| Task handler / command | Explicit outputs |
| Sub use case | Named return value |

### 7. Loops in Natural Language

```
Repeat the following for each element of _orderItems_ as _item_:
   1. Validate _item_
   2. Transform _item_ to target format

Loop from 0 to _count_ - 1 as _index_ and perform the following:
   1. Generate ID for _index_
   2. Collect into _results_
```

### 8. Natural Language Over Pseudo-code (Cockburn only)

**This applies only to the Cockburn style.** Write steps as sentences describing what happens. Avoid programming constructs.

**Do:**
```
Remove characters from _valueTo_ where _valueMask_ contains '-'; call it _lastIndexString_
Fetch the shopping cart resource from Shopping Cart service; call it _cart_
Convert _@type_ child node of _payload_ to string; call it _payloadType_
```

**Don't:**
```
for each char in valueTo: if valueMask[i] != '-': append to result
IF condition THEN X ELSE Y
```

**The pseudo-code style explicitly allows IF/THEN constructs** — see `pseudo-code-style.md` for the full language.
