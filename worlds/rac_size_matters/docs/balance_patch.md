# Balance patch

`balance_patch` is a generation toggle, default **off**. It is serialized in slot
data and applied by the native runtime. Older slots without the key remain off.
It does not change item placement or access rules.

The source is the supplied `core/patches/8661F7BA_UPDATE.pnach`, Update 1.03 by
usernamecipher. The file is retained unchanged for attribution and comparison.
The client uses checked native patches rather than asking PCSX2 to load this US
cheat on a different release. Supported serials are SCUS-97615, SCES-55019 and
SCPS-15120.

## Regional mapping

`balance_data.py` groups edits into named planet tables and `PatchGroup` records
for each weapon or movement effect. Each record labels its regional offsets,
original retail words, replacements, and optional boss overrides. Damage groups
list levels 1–4 in order with `stride=0x10`; instruction groups use consecutive
words. `f32(...)` keeps gameplay values readable while encoding exact float32
words. EU/JP word lists inherit US unless an explicit override is present.
Unusual rounded float words remain hexadecimal to preserve their exact bits.

The small immutable records in `balance_types.py` validate group lengths and
alignment, then expand groups into named individual edits for the runtime.
To update an effect, edit its named group rather than the expansion logic. Keep
regional offsets and original signature words tied to verified retail data;
update the corresponding fixtures if those signatures change.

Offsets are relative to the loaded SNR2 module. They were derived from the local
regional ISOs' `LVL/LEVEL_XX.REL` files. Weapon table layouts were matched using
surrounding records; code sites were matched by instruction sequences with
relocation operands normalized. Exact context matches were checked against the
resulting offsets. The bounded test fixtures contain surrounding retail bytes.
Retail module hashes are recorded in `balance_patch_sources.json`.

The patch covers source levels 01, 02, 03, 05, 06, 07, 08, 09, 10 and 15.
Levels absent from the source are left alone. Level 15 is handled even though
it does not have a normal Ratchet planet address-map entry.

EU retail per-frame Acid Bomb trails, Scorcher/Laser Tracer damage and helipack
movement use 1.2 times the US/JP values for 50 Hz. The replacements preserve
that compensation. Timers count native HUD frames, not client polls.

The supplied Inside Clank movement entries mistakenly reuse Dayni Moon's
absolute addresses. This port targets the matching Inside Clank routines.
Original words are checked before any writes, and installation rolls back on
failure. A changed option requests a level reload rather than removing an
executing callback. Disconnecting the client does not undo loaded native code;
restart the game if returning to completely unpatched standalone play.

## Conditional effects

Ryllus retains the source's four-health trigger and 60-frame delay before
clearing the two gadgetbot door event states. After object initialization, the
client finds the door by its scene transform and paired event references.
It does not assume that JP runtime allocations have the same absolute address.
The relevant scene asset (`86880e3e`) is identical in US and JP, and the entire
EU Ryllus WAD is identical to US. Both actor references are checked again by the
native callback before changing the event states.

Quodrona uses the source's upper-halfword health comparisons, applying the boss
damage values inside that interval and the normal patched values outside it.
After 45 boss frames, the ammo reminder is shown once through the existing
native notification renderer. It waits for any current AP receipt to finish.
This replaces the source's fixed-address English boss-label overwrite and works
with the regional text layouts. The source itself does not refill ammunition;
the reminder describes the game's refill behaviour.

Counters and callback code live in reserved vendor storage, with no use of the
source's unowned scratch addresses. The conditional effects require the native
vendor storage; its internal debug switch must stay enabled. The normal player
option does not require Experimental Skins or multiplayer skin support.

## Validation

Automated checks cover all 30 regional level combinations, exact restoration,
changed-code/game rejection, partial-write rollback, executed boss thresholds,
normal damage restoration, frame timers, relocated door discovery, notification
coexistence and generation/slot-data defaults. The US Pokitaru and Ryllus static
edits also matched existing saved RAM byte for byte; combined native startup
passed on those captures with no overlapping patch ranges.

This is offline validation against retail files and saved memory, plus execution
of the generated callback instructions in the test MIPS interpreter. A complete
live gameplay tour of this balance patch has not been performed.
