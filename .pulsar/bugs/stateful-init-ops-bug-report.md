# Stateful: `StateList<T>.GetInitializationOperations()` returns the empty `_initOps` field instead of the locally-populated `ops` array — silently drops every initial element delivered to subscribers

**Repo:** `github.com/epjecha/StatefulUnity` (`Assets/Package`)
**Pinned hash at time of investigation:** `18058ab1ef1f35409695c10d057f3924745834e4`
**Affected file:** `Runtime/StateTypes/StateList.cs`
**Symptom severity:** loud on IL2CPP/Android — throws `System.ArgumentOutOfRangeException` from `List<T>.Insert/RemoveAt` in any subscriber that mirrors the source list (e.g. `ObserveThing.IndexOfObservable<T>`).
**Platform where observed:** Unity 6000.0.66f1, Android, IL2CPP, ARCore mobile build.

---

## TL;DR

`StateList<T>.GetInitializationOperations()` builds a local `ops` array, fills it with one `OpType.Add` per existing element, and then returns the unrelated `_initOps` field — a `List<StateOpArgs<T>>` declared on line 69 and **never written to anywhere**. The local `ops` is discarded. Every subscriber that goes through `Observable<T>.Subscribe`'s init-replay receives an empty list, regardless of how many elements the `StateList` actually contains.

Downstream operators that mirror the source list — `ObserveThing.IndexOfObservable<T>` is the one that surfaced this, but any operator with the same shape would — start with `_list.Count == 0` instead of `== source.Count`. The first live `onAdd(N, element)` or `onRemove(N, element)` for `N > 0` then throws `ArgumentOutOfRangeException` from `List<T>.Insert(N, …)` or `RemoveAt(N)`.

The commit pinned here has the message `"fix init operations bug and test"`. The fix attempt did the right thing in `CombineStateObservable.cs:152` (`return ops;`) but typo'd `return _initOps;` in three sibling files: `StateList.cs:96`, `StateObject.cs:50`, and `StateValue.cs:90`. The `StateObject` one is harmless (`StateObject` has no per-element init replay; an empty list is correct). The `StateValue` one is structurally identical to `ObservableValueBase._initOperations` — a shared single-element list that gets mutated in place — and is a latent foot-gun. The `StateList` one is the bug that throws.

**Fix:** return `ops` (the local) from `GetInitializationOperations` in `StateList.cs:96`. Delete the dead `_initOps` field on line 69 while you're there.

```diff
 protected override IReadOnlyList<StateOpArgs<T>> GetInitializationOperations()
 {
     var ops = new StateOpArgs<T>[_list.Count];

     for (int i = 0; i < _list.Count; i++)
     {
         var element = _list.ElementAndIdAt(i);
         ops[i] = new StateOpArgs<T>(this, OpType.Add, element.value, element.id, i, element.value);
     }

-    return _initOps;
+    return ops;
 }
```

We patched this in our local PackageCache, rebuilt the APK, installed on the test device, and the `ArgumentOutOfRangeException` flood is gone. The in-room state machine (avatars, `roomStateInitialized: True`, high-frequency-sync wiring) runs cleanly.

---

## Reproduction shape

Any time a `StateList<T>` has elements at the moment a derived operator subscribes — typical for `App.state.rooms` after Supabase polling has populated it once and the UI then builds per-room observation chains:

```csharp
// somewhere in the UI build, per existing room:
App.state.loadedDemoScenes
    .ObservableSelect(x => x.Key)
    .ObservableContains(roomData.demoScene)   // spawns an IndexOfObservable<string>
    .Subscribe(...);
```

`ObservableContains` is implemented in terms of `ObservableIndexOf`, which constructs an `IndexOfObservable<T>`. `IndexOfObservable.ctor` synchronously subscribes to the source list, expecting init-replay to fire `HandleAdd(0,A), HandleAdd(1,B), …` for every existing element so its internal `_list` mirrors the source. Without that replay, `_list` stays empty. The next live operation (`onAdd(N>0, X)` or `onRemove(N>0, X)`) hits `_list.Insert(N, X)` with `_list.Count == 0` and throws.

The error is caught by the framework's `Settings.DefaultExceptionHandler` and routed to the consumer's unhandled-exceptions log group (in our case `LogGroup.UnhandledExceptions`), so the app doesn't crash — but each thrown frame leaves an `IndexOfObservable` in a permanently desynced state. Downstream `Observable<int>` outputs (`-1` for "not contained" vs. an actual index) become incorrect, so per-room filtering (`AppUI.cs:111–128` in our app: "is the demo scene available?") returns wrong results for whichever rooms got their IndexOfObservable populated via init-replay rather than via live ops.

---

## Cascade trace

For a `StateList<T>` `source` with internal `_list = [A, B, C, D]` at subscribe time:

1. `IndexOfObservable<T>.ctor` calls `source.Subscribe(IListObserver<T>)`.
2. That overload (`StateList.cs:313–344`) wraps the observer in `new Observer<StateOpArgs<T>>(onOperation: ops => { … })` and forwards to the inherited `Observable<StateOpArgs<T>>.Subscribe`.
3. The base `Subscribe` calls `observer.OnOperation(GetInitializationOperations())`.
4. `GetInitializationOperations()` (line 86) allocates a local `ops` array of size 4, fills it with 4 `OpType.Add` records, **and returns `_initOps`** — a separate field, count 0.
5. The wrapping `Observer<StateOpArgs<T>>.onOperation` lambda receives the empty list. The `if (ops == null)` branch on line 317 — which would have correctly fallen back to iterating `_list.ElementsWithIds` directly — is not taken (the list is empty, not null). The `foreach (var op in ops)` block iterates zero items. The subscriber's `OnAdd` is never called.
6. `IndexOfObservable._list` remains `[]`. `_index` remains `-1`. The receiver's initial `OnNext(-1)` fires.
7. Later, a real mutation to `source` (e.g. `_list.Add(E)`) enqueues `onAdd(4, E)`. `Observable<T>.SendNext` delivers it. The wrapped lambda iterates the one-element batch, calls `observer.OnAdd(id, 4, E)`, which reaches `IndexOfObservable.HandleAdd(4, E)`.
8. `_list.Insert(4, E)` — `_list.Count == 0`, so `4 > Count` → `ArgumentOutOfRangeException: Index must be within the bounds of the List`.

The `_initOps` field is declared:

```csharp
private List<StateOpArgs<T>> _initOps = new List<StateOpArgs<T>>();
```

It is read once (the buggy return) and never written. Dead state surviving from a previous shared-mutable design.

---

## Empirical evidence

Loki capture from the unfixed build, right after the user joined a room (16 pre-existing rooms in `App.state.rooms`):

- **10 `System.ArgumentOutOfRangeException` events**, all routed through `LogGroup.UnhandledExceptions`.
- 7 with `List`1.Insert(Int32, T)` at the top of the exception stack (HandleAdd flavor), 3 with `List`1.RemoveAt(Int32)` (HandleRemove flavor).
- Bottom of every exception stack:
  ```
  ObserveThing.IndexOfObservable`1.HandleAdd(Int32, T)
  ObserveThing.ListObserver`1.OnAdd(UInt32, Int32, T)
  FofX.Stateful.StateList`1.+[Anonymous_](IReadOnlyList`1)
  ObserveThing.Observer`1.OnOperation(IReadOnlyList`1)
  ObserveThing.Observable`1+ObserverData.SendNext()
  ObserveThing.ObservationContext.DrainPendingImmediateObserverQueue()
  ```
- Errors fire in two bursts ~5 seconds apart, correlated with the user-driven `App.state.rooms` and `App.state.loadedDemoScenes` mutations triggered by joining a room.

After patching `return _initOps;` → `return ops;` in `StateList.cs:96`, rebuilding the APK, and reinstalling:

- 0 `IndexOfObservable` references in the next Loki run.
- 0 `ArgumentOutOfRangeException` events.
- The room-join state machine completes: `roomStateInitialized: True`, avatar added at `root/scene/players/1`, high-frequency-sync wiring set up for `localPosition`/`localRotation`. No state-list desync.

(The two `error`-level entries in that post-fix run were transient `NameResolutionFailure` during a Keycloak login retry — unrelated to this bug.)

---

## Why it's easy to introduce this pattern

Two patterns combine:

1. **Shared mutable `_initOps` was previously the intended design** across the package's observable bases (`ObservableListBase`, `ObservableSetBase`, `ObservableValueBase`, and the Stateful types here). The shared-list-cleared-and-refilled pattern is what the corresponding `observething-bug-report.md` (also in this directory, against the upstream `ObserveThing` package) called out. When fixing that, the natural change is "stop reusing the field, allocate fresh." If you do that at five sites, four of which used `_initOps.Clear(); _initOps.Add(...); return _initOps;` and one of which used `_initOps[0] = _value; return _initOps;`, it is easy to:
   - Rewrite the body to build a local `ops`,
   - Forget to update the `return _initOps;` line,
   - Leave the now-dead `_initOps` field declared above.
2. **The signature is `IReadOnlyList<T>`, so the C# compiler accepts `return _initOps;` (a `List<T>`) without complaint** — same type. There is no compiler signal that `ops` was built but never used.

Suggested guard against recurrence:

- **Stop declaring the shared field at all** in the sites where the fix is to allocate fresh. The presence of a stale `_initOps` field is what made the typo possible. Removing it would have caused a compile error on the buggy return statement.
- **A `[return: NotNull]` analyzer or a test that asserts `GetInitializationOperations().Count == _list.Count`** for a non-empty list would catch this.

---

## Related: `StateValue<T>.GetInitializationOperations()` (`StateValue.cs:88–91`) and `StateObject.GetInitializationOperations()` (`StateObject.cs:48–51`)

Both still use the `_initOps` field-return pattern. Status differs:

- **`StateObject.cs:50`** — `_initOps` is always empty by design (the `StateObject` has children but no add/remove init replay). Returning the empty list is correct. The field can be deleted (just `return Array.Empty<StateOpArgs<object>>();`) for hygiene, but it isn't a bug.
- **`StateValue.cs:90`** — same shape as `ObservableValueBase._initOperations` in upstream `ObserveThing`. Mutates `_initOps[0] = new StateOpArgs<T>(this, OpType.Set, value);` and returns the shared one-element list. The outer foreach in any subscriber's `OnOperation` has already iterated past index 0 by the time a re-entrant call could mutate `_initOps[0]`, so we have not observed a concrete bug — but the foot-gun is the same one the `observething-bug-report.md` flagged. Suggested fix: return `new[] { new StateOpArgs<T>(this, OpType.Set, value) };` and delete the field.

---

## Notes

- The fix lands cleanly in the local PackageCache for ad-hoc verification. The durable fix is upstream + a `packages-lock.json` hash bump in each consumer (`apps/MakeItSing`, `apps/AndroidMobile`, `packages/unity/Placeframe`).
- The `Tests/` directory in this package version was added alongside the buggy commit ("fix init operations bug and test") — whatever those tests exercise, they do not catch the case "subscribe to a `StateList` with pre-existing items and expect every item to be re-emitted." That would have caught this immediately.
- This bug is silent on init-replay itself (subscriber simply gets zero ops). The loud `ArgumentOutOfRangeException` only fires once a live mutation happens against a subscriber that mirrors the source. Code paths that subscribe to a `StateList` *before* it has any items will appear to work fine until the source crosses some threshold; that explains why it was easy to ship.
