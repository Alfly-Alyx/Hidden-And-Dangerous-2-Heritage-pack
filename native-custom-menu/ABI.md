# Native GUI lifecycle (stock Sabre Squadron 1.12)

These addresses are checked against `tmp/stock-menu-analysis.bin` (image data
starts at VA `0x401000`). Offline tests are not evidence of rendered output.

## Definitions and live controls are different objects

`0x615360` allocates a 0x40-byte definition. Its routing ID is at +8.
`0x614e80` and `0x614f10` append initialization messages to the definition.
The mission builder `0x6392b0` runs during preload, with `MenuView == 0`.
Opening a category does not call this builder again.
Definitions are subsequently released; copy their routing IDs during preload,
not by dereferencing their old addresses on later refreshes. The copied IDs in
`MenuCategoryIds` are the durable handles, not `MenuCategoryControls`.

The runtime object's routing ID is at +0x60, and its visibility byte is at
+0x65. A definition must never be passed to a runtime or scene vtable method,
and a callback must not overwrite the live routing ID to encode an action.

## Runtime messages

`0x615a90` takes ECX = `0x8ae590`, one stack argument pointing to six DWORDs,
and returns with `ret 4`. It copies the message synchronously:

`{ targetId, eventId, parameter1, parameter2, 0, 0 }`

- `0x01000003`: show control and its scene node.
- `0x01000004`: hide control and its scene node, including generated text.
- `0x01000001` / `0x01000002`: disable / enable (separate from visibility).
- `0x01000015`: localized text (parameter1 = style, parameter2 = string ID).

Show/hide dispatch is verified at `0x65d060`, `0x65ca80`, `0x65cab0`.
The renderer checks +0x65 at `0x661fa0`.

The stock refresh `0x63ab60` queues changes before returning at `0x63af06`.
The custom layout must queue its visibility changes after this refresh.

### Hidden list groups need an explicit row refresh

The real flat list uses vtable `0x814a08`, not a text-button vtable. Handler
`0x659d50` maintains active children at +8/+0xc and inactive children at
+0xa4/+0xa8. `0x02000085` hides/removes active rows; `0x02000083` restores a
row to the active collection, but queues its refresh only if +0x65 is nonzero
(`0x65a060`). Adding rows while the category selector hides the list therefore
leaves those rows hidden. SHOW only reveals the parent (`0x6564b3`), and does
not reflow/reveal children. Queue `0x0200002c` for `0x14800000` **after** SHOW.
The native refresh runs `0x656a20`, which reveals the active visible range.

`test_native_menu_rows.py` reproduces the empty-list failure with the stock
row builder and list handler; font projection and scene calls remain doubles.
It failed on the pre-fix module and passes with the ordered row refresh.
This is stronger than testing parent visibility but still is not a pixel test.

## Mission browser target IDs

| ID | Element |
|---|---|
| 0x14100000 | Title |
| 0x14200000 | Preview |
| 0x14300000 | Description |
| 0x14400000 | Start |
| 0x14500000 | Primary bottom Back (`bexit`) |
| 0x14600000 | Scrollbar |
| 0x14700000 | Campaign group |
| 0x14800000 | Mission group |
| 0x14900000 | List caption |
| 0x14a00000 | Version |
| 0x14b00000 | Resume |
| 0x14c00000 | Secondary Back, hidden by default (`bexit01`) |

Custom categories are appended after stock definitions; copy their assigned
IDs from definition +8 before the definitions are released.

## Back and category input

The instruction at `0x639aef` initializes the secondary Back with HIDE. It is
not a navigation event and must remain stock.

Primary Back is bound with `0x06001003`. A click strips the binding flags in
`0x65d270`, producing application event `0x02000003`. The global dispatcher
consumes this at `0x66cd70`, before the per-screen handler `0x638e21`.

Only intercept global Back while the top live screen is the mission browser.
Nested screens must retain their native return behavior. Category callbacks
post private application events with target zero; a nonzero target would
dispatch to a runtime widget instead of the application handler.
